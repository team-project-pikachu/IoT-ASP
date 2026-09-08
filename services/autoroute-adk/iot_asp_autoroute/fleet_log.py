"""Structured fleet telemetry logs (#22) — enrich, scrub, record, store, aggregate.

One fixed-shape, PII-scrubbed JSON Lines record per telemetry heartbeat / autoroute
decision under ``meta/logs/<node>/<YYYY-MM-DD>.jsonl`` plus a pure aggregator and a
documented retention plan for the Colab handoff (#17 / #26).

Stdlib only (``zoneinfo`` for America/New_York). Imports ``clamps``, ``priors`` and
``sudden_freq`` (all stdlib) — never ``tools`` / ``vib_anomaly`` (numpy / scipy) and
never ``google.cloud.storage`` at module level. Never writes ``meta/patches/`` or
``meta/telemetry/``; ``clamps.validate_patch`` stays the only policy authority.

Secrets by **name** only (``GOOGLE_CLOUD_PROJECT``, ``IOT_ASP_GCS_BUCKET``); no env
values are ever printed or logged.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import gcs_io
from .clamps import BAND_LF, SCHEMA_VERSION, band_limits
from .priors import normalize_vib_class
from .sudden_freq import is_sudden_freq_event, normalize_algo

try:  # tzdata may be missing on slim containers → nightNY=False + one warn record
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    NY_TZ: Any = ZoneInfo("America/New_York")
except (ImportError, ZoneInfoNotFoundError):  # pragma: no cover - environment dependent
    NY_TZ = None

KIND = "fleet_log"
NIGHT_HOURS = frozenset(range(22, 24)) | frozenset(range(0, 7))
LEVELS = ("debug", "info", "warn", "error")
BANDS = ("17-23k", "10-20")
ALARM_STATES = ("armed", "triggered", "sustaining", "cleared")
DEFAULT_POWER = "ac120"
MSG_MAX = 240
WIRE_TS_FMT = "%Y-%m-%dT%H:%M:%SZ"
FILE_TS_FMT = "%Y-%m-%dT%H-%M-%SZ"
LOG_PREFIX = "meta/logs/"
AGG_PREFIX = "meta/logs-agg/"
RMW_RETRIES = 3

RECORD_KEYS: list[str] = [
    "kind",
    "schemaVersion",
    "ts",
    "level",
    "event",
    "deviceId",
    "band",
    "power",
    "nightNY",
    "lfArmed",
    "lfDriveCapable",
    "lfGate",
    "algo",
    "vibClass",
    "suddenFreq",
    "suddenState",
    "holdManual",
    "peakHz",
    "absA",
    "micEnergy",
    "impulse",
    "volBlast",
    "alarmState",
    "msg",
]

# PII denylist (invariant 7: no site PII). Three tiers, all case-insensitive:
#   * PII_DENY_EXACT      — whole key (lowercased) equals an entry.
#   * PII_DENY_SUBSTRINGS — long, unambiguous words matched anywhere in the key once
#                           separators are stripped ("emailaddress", "address1", "gpslat",
#                           "transcription", "recordingUrl", "ipaddr" all drop).
#   * PII_DENY_TOKENS     — short words matched only as whole tokens (split on `_`, `-`,
#                           whitespace and camelCase) so `latency`, `long`, `ipc`, `filename`
#                           survive; compound lowercase spellings (`username`, `latlng`, …)
#                           are listed explicitly because they never split.
# `phone` is a substring match too, except inside `microphone` / `headphone` / `earphone`.
PII_DENY_EXACT = frozenset({"recordinguri", "recording_uri", "latitude", "longitude"})
PII_DENY_SUBSTRINGS = ("addr", "street", "email", "transcript", "speech", "recording", "gps")
PII_DENY_TOKENS = frozenset(
    {
        "address",
        "street",
        "name",
        "email",
        "phone",
        "lat",
        "lon",
        "gps",
        "ip",
        "transcript",
        "speech",
        "recording",
        # compound spellings that never split into tokens
        "username",
        "fullname",
        "firstname",
        "lastname",
        "surname",
        "nickname",
        "displayname",
        "realname",
        "latlon",
        "latlng",
        "lonlat",
        "lnglat",
        "ipaddr",
        "ipv4",
        "ipv6",
        "geo",
        "geolocation",
        "location",
        "coords",
        "coordinates",
        "zip",
        "zipcode",
        "postal",
        "postcode",
        "postalcode",
    }
)
_PHONE_RE = re.compile(r"(?<!micro)(?<!head)(?<!ear)phone")

_FALSE_STRINGS = frozenset({"", "0", "false", "no", "off", "none", "null"})
_NODE_SAFE = re.compile(r"[^A-Za-z0-9_.-]")
_FLAT = re.compile(r"[^a-z0-9]+")
_CAMEL = re.compile(r"([a-z0-9])([A-Z])")
_ACRONYM = re.compile(r"([A-Z]+)([A-Z][a-z])")
_tz_warn_emitted = False


# ── timestamps ──────────────────────────────────────────────────────────────


def parse_ts(ts: Any) -> datetime | None:
    """ISO-8601 (Z/offset/naive=UTC), filename form, epoch ms (>1e12) or s → aware UTC."""
    if ts is None or isinstance(ts, bool):
        return None
    if isinstance(ts, (int, float)):
        return _from_epoch(float(ts))
    if isinstance(ts, datetime):
        dt = ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    if not isinstance(ts, str):
        return None
    s = ts.strip()
    if not s:
        return None
    try:
        return _from_epoch(float(s))
    except ValueError:
        pass
    iso = s[:-1] + "+00:00" if s.endswith(("Z", "z")) else s
    dt: datetime | None = None
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        try:
            dt = datetime.strptime(s, FILE_TS_FMT)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _from_epoch(v: float) -> datetime | None:
    if not math.isfinite(v):
        return None
    if v > 1e12:
        v = v / 1000.0
    try:
        return datetime.fromtimestamp(v, timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def to_wire_ts(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime(WIRE_TS_FMT)


def night_ny(ts: Any) -> bool:
    """True when the America/New_York local hour of ``ts`` is in [22,24) ∪ [0,7)."""
    dt = parse_ts(ts)
    if dt is None or NY_TZ is None:
        return False
    return dt.astimezone(NY_TZ).hour in NIGHT_HOURS


# ── enrichment ──────────────────────────────────────────────────────────────


def infer_band(t: dict[str, Any]) -> str:
    """``10-20`` when the tag says so or ``fMin <= 100`` (via clamps.band_limits)."""
    return "10-20" if band_limits(t) == BAND_LF else "17-23k"


def _key_tokens(key: str) -> list[str]:
    snake = _CAMEL.sub(r"\1_\2", _ACRONYM.sub(r"\1_\2", key))
    return [tok for tok in re.split(r"[_\-\s]+", snake.lower()) if tok]


def is_pii_key(key: Any) -> bool:
    """True when ``key`` names site PII (exact, substring or whole-token match)."""
    k = str(key)
    low = k.lower()
    if low in PII_DENY_EXACT:
        return True
    flat = _FLAT.sub("", low)
    if any(sub in flat for sub in PII_DENY_SUBSTRINGS) or _PHONE_RE.search(flat):
        return True
    return any(tok in PII_DENY_TOKENS for tok in _key_tokens(k))


def scrub_pii(obj: Any) -> tuple[Any, list[str]]:
    """Return (clean copy, sorted dropped key names). Dropped *values* are discarded."""
    dropped: list[str] = []

    def walk(value: Any) -> Any:
        if isinstance(value, dict):
            out: dict[str, Any] = {}
            for k, v in value.items():
                if is_pii_key(k):
                    dropped.append(str(k))
                    continue
                out[k] = walk(v)
            return out
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, tuple):
            return [walk(v) for v in value]
        return copy.deepcopy(value)

    return walk(obj), sorted(dropped)


def _as_bool(v: Any) -> bool:
    if isinstance(v, str):
        return v.strip().lower() not in _FALSE_STRINGS
    return bool(v)


def _alarm_state(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip().lower()
    return s if s in ALARM_STATES else None


def _vib_class(v: Any) -> str:
    """``priors.normalize_vib_class`` for any wire value (non-strings → ``none``, never raises)."""
    return normalize_vib_class(v if isinstance(v, str) else None)


def enrich_telemetry(t: dict[str, Any]) -> dict[str, Any]:
    """Pure: scrub PII, then fill band / power / nightNY / lfArmed / lfDriveCapable / lfGate.

    Never raises on malformed phone values: a non-string ``vibClass`` / ``power`` / ``band``
    is treated as absent (``tools.ingest_telemetry`` calls this before any write).
    """
    src = t if isinstance(t, dict) else {}
    out, dropped = scrub_pii(src)
    if out.get("band") not in BANDS:
        out["band"] = infer_band(out)
    power = out.get("power")
    out["power"] = power.strip() if isinstance(power, str) and power.strip() else DEFAULT_POWER
    out["nightNY"] = night_ny(out.get("ts"))
    out["lfArmed"] = _as_bool(out.get("lfArmed", False))
    out["lfDriveCapable"] = _as_bool(out.get("lfDriveCapable", False))
    out["vibClass"] = _vib_class(out.get("vibClass"))
    out["lfGate"] = bool(out["lfArmed"] and out["lfDriveCapable"] and out["vibClass"] == "infra_felt")
    if dropped:
        out["piiDropped"] = int(out.get("piiDropped") or 0) + len(dropped)
    return out


# ── records ─────────────────────────────────────────────────────────────────


def _num(v: Any) -> int | float | None:
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return v if math.isfinite(v) else None
    if isinstance(v, str):
        try:
            f = float(v)
        except ValueError:
            return None
        return f if math.isfinite(f) else None
    return None


def log_record(
    level: str,
    event: str,
    telemetry: dict[str, Any],
    msg: str = "",
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Fixed-order ``fleet_log`` record (``list(record) == RECORD_KEYS``)."""
    lvl = str(level or "").strip().lower()
    if lvl not in LEVELS:
        raise ValueError(f"level must be one of {LEVELS}, got {level!r}")
    t = enrich_telemetry(telemetry)
    dt = parse_ts(t.get("ts")) or (now or datetime.now(timezone.utc))
    sudden = t.get("suddenFreq") is True or is_sudden_freq_event(t)
    state = t.get("suddenState")
    abs_a = t.get("absA", t.get("a"))
    return {
        "kind": KIND,
        "schemaVersion": SCHEMA_VERSION,
        "ts": to_wire_ts(dt),
        "level": lvl,
        "event": str(event or ""),
        "deviceId": str(t.get("deviceId") or t.get("nodeId") or "node1"),
        "band": t["band"],
        "power": str(t["power"]),
        "nightNY": bool(t["nightNY"]),
        "lfArmed": bool(t["lfArmed"]),
        "lfDriveCapable": bool(t["lfDriveCapable"]),
        "lfGate": bool(t["lfGate"]),
        "algo": normalize_algo(t.get("algo")),
        "vibClass": t["vibClass"],
        "suddenFreq": bool(sudden),
        "suddenState": None if state is None else str(state),
        "holdManual": bool(t.get("holdManual", False)),
        "peakHz": _num(t.get("peakHz")),
        "absA": _num(abs_a),
        "micEnergy": _num(t.get("micEnergy")),
        "impulse": _as_bool(t.get("impulse", False)),
        "volBlast": _as_bool(t.get("volBlast", False)),
        "alarmState": _alarm_state(t.get("alarmState")),
        "msg": str(msg or "")[:MSG_MAX],
    }


def safe_node(node: Any) -> str:
    """Object-name-safe node id: ``[A-Za-z0-9_.-]`` only, never ``.``/``..``/empty (→ ``node1``).

    Shared with ``tools.ingest_telemetry`` so a phone-controlled ``deviceId`` can never form a
    ``..`` path segment under ``meta/telemetry/`` or ``meta/logs/``.
    """
    s = _NODE_SAFE.sub("_", str(node or "")).lstrip(".")
    return s or "node1"


_safe_node = safe_node  # backward-compatible private alias


def safe_ts(ts: Any, *, now: datetime | None = None) -> str:
    """Filename-form timestamp (``%Y-%m-%dT%H-%M-%SZ``) from any wire ``ts``; unparseable → now."""
    dt = parse_ts(ts) or (now or datetime.now(timezone.utc))
    return dt.astimezone(timezone.utc).strftime(FILE_TS_FMT)


def record_path(node: str, ts: Any) -> str:
    dt = parse_ts(ts) or datetime.now(timezone.utc)
    return f"{LOG_PREFIX}{safe_node(node)}/{dt.strftime('%Y-%m-%d')}.jsonl"


def _dumps_line(record: dict[str, Any]) -> str:
    # ensure_ascii=True: every non-ASCII code point (incl. U+2028/U+2029/U+0085, which
    # str.splitlines() treats as line breaks) is \u-escaped, so one record == one '\n' line.
    return json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n"


def _dry_root() -> Path:
    env = os.environ.get("IOT_ASP_AUTOROUTE_DRY_ROOT")
    return Path(env) if env else Path(gcs_io.DRY_ROOT)


def _tz_warning_record(record: dict[str, Any]) -> dict[str, Any] | None:
    """One-time ``warn``/``tz_unavailable`` record when America/New_York is missing."""
    global _tz_warn_emitted
    if NY_TZ is not None or _tz_warn_emitted:
        return None
    _tz_warn_emitted = True
    return log_record(
        "warn",
        "tz_unavailable",
        {"deviceId": record.get("deviceId"), "ts": record.get("ts")},
        msg="zoneinfo America/New_York unavailable; nightNY forced False (add tzdata)",
    )


def write_log_record(node: str, record: dict[str, Any]) -> dict[str, Any]:
    """Append one record to ``meta/logs/<node>/<YYYY-MM-DD>.jsonl`` via the gcs_io policy.

    Dry-run: local append. Live GCS: objects are immutable (no append) so the writer
    does read-modify-write guarded by ``if_generation_match``; after ``RMW_RETRIES``
    precondition failures the line goes to a ``.part.jsonl`` side-file so nothing is lost.
    Never raises — returns ``{ok: False, error}`` so a log failure cannot alter a decision.
    """
    try:
        path = record_path(node, record.get("ts"))
        lines = ""
        extra = _tz_warning_record(record)
        if extra is not None:
            lines += _dumps_line(extra)
        lines += _dumps_line(record)
        if gcs_io.is_dry_run():
            local = _dry_root() / path
            local.parent.mkdir(parents=True, exist_ok=True)
            with local.open("a", encoding="utf-8") as fh:
                fh.write(lines)
            return {"ok": True, "uri": f"file://{local}", "path": path, "mode": "append"}
        return _write_live(path, lines, record)
    except Exception as exc:  # noqa: BLE001 - observability must never propagate
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "path": None}


def emit_log(
    node: str,
    level: str,
    event: str,
    telemetry: dict[str, Any],
    msg: str = "",
) -> dict[str, Any]:
    """``write_log_record(node, log_record(...))`` with the record build inside the guard.

    Preferred hook for ``tools.py``: never raises, even on malformed telemetry or a bad
    ``level`` — returns ``{ok: False, error}`` so observability cannot alter a decision.
    """
    try:
        record = log_record(level, event, telemetry, msg=msg)
    except Exception as exc:  # noqa: BLE001 - observability must never propagate
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "path": None}
    return write_log_record(node, record)


def _write_live(path: str, lines: str, record: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover - needs GCS
    from google.api_core.exceptions import PreconditionFailed  # type: ignore
    from google.cloud import storage  # type: ignore

    client = storage.Client(project=gcs_io.PROJECT)
    bucket = client.bucket(gcs_io.BUCKET)
    ctype = "application/x-ndjson"
    for _ in range(RMW_RETRIES):
        blob = bucket.blob(path)
        if blob.exists():
            blob.reload()
            generation = int(blob.generation or 0)
            body = blob.download_as_text()
        else:
            generation, body = 0, ""
        if body and not body.endswith("\n"):
            body += "\n"
        try:
            blob.upload_from_string(body + lines, content_type=ctype, if_generation_match=generation)
            return {"ok": True, "uri": f"gs://{gcs_io.BUCKET}/{path}", "path": path, "mode": "rmw"}
        except PreconditionFailed:
            continue
    safe_ts = str(record.get("ts") or to_wire_ts(datetime.now(timezone.utc))).replace(":", "-")
    side = path[: -len(".jsonl")] + f".{safe_ts}.part.jsonl"
    bucket.blob(side).upload_from_string(lines, content_type=ctype, if_generation_match=0)
    return {"ok": True, "uri": f"gs://{gcs_io.BUCKET}/{side}", "path": side, "mode": "rmw-fallback"}


def _parse_lines(text: str) -> tuple[list[dict[str, Any]], int]:
    out: list[dict[str, Any]] = []
    skipped = 0
    # Split on '\n' only — never str.splitlines(), which also breaks on U+2028/U+2029/U+0085
    # and would shatter a record whose string fields carry them.
    for line in text.split("\n"):
        line = line.rstrip("\r")
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        if isinstance(obj, dict):
            out.append(obj)
        else:
            skipped += 1
    return out, skipped


def _log_names(node: str, date: str | None) -> list[str]:
    """Object names (``meta/logs/<node>/…jsonl``), ascending; ``.part.jsonl`` included."""
    prefix = f"{LOG_PREFIX}{safe_node(node)}/"
    if gcs_io.is_dry_run():
        root = _dry_root() / prefix
        if not root.is_dir():
            return []
        names = sorted(prefix + p.name for p in root.iterdir() if p.is_file() and p.name.endswith(".jsonl"))
    else:  # pragma: no cover - needs GCS
        from google.cloud import storage  # type: ignore

        client = storage.Client(project=gcs_io.PROJECT)
        names = sorted(b.name for b in client.list_blobs(gcs_io.BUCKET, prefix=prefix) if b.name.endswith(".jsonl"))
    if date:
        names = [n for n in names if n.rsplit("/", 1)[-1].startswith(f"{date}.")]
    return names


def read_log_records_with_stats(node: str, date: str | None = None) -> tuple[list[dict[str, Any]], int]:
    records: list[dict[str, Any]] = []
    skipped = 0
    for name in _log_names(node, date):
        if gcs_io.is_dry_run():
            text = (_dry_root() / name).read_text(encoding="utf-8")
        else:  # pragma: no cover - needs GCS
            from google.cloud import storage  # type: ignore

            text = storage.Client(project=gcs_io.PROJECT).bucket(gcs_io.BUCKET).blob(name).download_as_text()
        recs, bad = _parse_lines(text)
        records.extend(recs)
        skipped += bad
    return records, skipped


def read_log_records(node: str, date: str | None = None) -> list[dict[str, Any]]:
    """All records for ``node`` (``date`` = ``YYYY-MM-DD`` or ``None`` = every date)."""
    return read_log_records_with_stats(node, date)[0]


# ── aggregation ─────────────────────────────────────────────────────────────


def _bucket(value: Any) -> str:
    return "unknown" if value is None or value == "" else str(value)


def aggregate_records(
    records: list[dict[str, Any]],
    window_s: int = 300,
    node: str | None = None,
) -> dict[str, Any]:
    """Pure, order-independent summary of ``fleet_log`` records."""
    if window_s is None or window_s <= 0:
        raise ValueError("window_s must be > 0")
    recs = [r for r in records if isinstance(r, dict)]
    count = len(recs)
    by: dict[str, dict[str, int]] = {"algo": {}, "vibClass": {}, "band": {}, "level": {}}
    windows: dict[int, dict[str, int]] = {}
    epochs: list[float] = []
    sudden = hold = night = 0
    for r in recs:
        is_sudden = r.get("suddenFreq") is True
        sudden += is_sudden
        hold += bool(r.get("holdManual"))
        night += bool(r.get("nightNY"))
        for key, table in by.items():
            b = _bucket(r.get(key))
            table[b] = table.get(b, 0) + 1
        dt = parse_ts(r.get("ts"))
        if dt is None:
            continue
        epoch = dt.timestamp()
        epochs.append(epoch)
        start = int(math.floor(epoch / window_s) * window_s)
        w = windows.setdefault(start, {"count": 0, "sudden": 0})
        w["count"] += 1
        w["sudden"] += is_sudden
    node_id = node
    if node_id is None and recs:
        node_id = recs[0].get("deviceId")
    return {
        "node": node_id,
        "first_ts": to_wire_ts(datetime.fromtimestamp(min(epochs), timezone.utc)) if epochs else None,
        "last_ts": to_wire_ts(datetime.fromtimestamp(max(epochs), timezone.utc)) if epochs else None,
        "count": count,
        "sudden_count": sudden,
        "hold_fraction": round(hold / count, 4) if count else 0.0,
        "night_fraction": round(night / count, 4) if count else 0.0,
        "by_algo": dict(sorted(by["algo"].items())),
        "by_vibClass": dict(sorted(by["vibClass"].items())),
        "by_band": dict(sorted(by["band"].items())),
        "by_level": dict(sorted(by["level"].items())),
        "windows": [
            {
                "start": to_wire_ts(datetime.fromtimestamp(s, timezone.utc)),
                "end": to_wire_ts(datetime.fromtimestamp(s + window_s, timezone.utc)),
                "count": w["count"],
                "sudden": w["sudden"],
            }
            for s, w in sorted(windows.items())
        ],
    }


# ── retention plan (Colab handoff #17 / #26) ─────────────────────────────────


def retention_plan() -> dict[str, Any]:
    """Raw 30 d / aggregates 365 d / features governed by #17; patches are ADK-only."""
    return {
        "schemaVersion": SCHEMA_VERSION,
        "raw": {
            "prefix": LOG_PREFIX,
            "layout": "meta/logs/<node>/<YYYY-MM-DD>.jsonl (+ .part.jsonl fallbacks)",
            "format": "JSON Lines, UTF-8, one fleet_log record per line, fixed key order",
            "producer": "ADK tools.py (ingest_telemetry, process_sudden_freq)",
            "consumer": "Colab ETL (#17/#26), fleet_log_summary tool",
            "days": 30,
        },
        "aggregates": {
            "prefix": AGG_PREFIX,
            "layout": "meta/logs-agg/<node>/<YYYY-MM-DD>.json",
            "format": "one aggregate_records object (window_s=300)",
            "producer": "Colab ETL nightly 03:30 America/New_York, or fleet_log_summary on demand",
            "consumer": "Gemini Enterprise seats via features; dashboards",
            "days": 365,
        },
        "features": {
            "prefix": "meta/features/",
            "layout": "meta/features/<node>/<ts>.json",
            "producer": "Colab only (colab_etl.extract_features, features_live)",
            "consumer": "ADK / Gemini (never authoritative)",
            "days": "governed by #17",
        },
        "patches": {
            "producer": "ADK write_patch only; Colab/ETL and fleet_log never meta/patches/",
        },
        "lifecycle": {
            "rule": [
                {"action": {"type": "Delete"}, "condition": {"age": 30, "matchesPrefix": [LOG_PREFIX]}},
                {"action": {"type": "Delete"}, "condition": {"age": 365, "matchesPrefix": [AGG_PREFIX]}},
            ]
        },
        "apply": "gcloud storage buckets update gs://$IOT_ASP_GCS_BUCKET --lifecycle-file=<json>",
        "softDeleteNote": "Lifecycle Delete enters the bucket soft-delete window (default 7 d) before hard deletion",
        "colab": {
            "auth": "Colab userdata names only: GCP_SA_JSON, IOT_ASP_GCS_BUCKET",
            "reader": "iot_asp_autoroute.fleet_log.read_log_records (shared; skips malformed lines)",
            "aggregator": "iot_asp_autoroute.fleet_log.aggregate_records (pure stdlib)",
        },
    }


# ── demo / CLI ──────────────────────────────────────────────────────────────


def demo_telemetry(node: str = "node1") -> list[dict[str, Any]]:
    """12 offline heartbeats: 2026-01-15T11:55:00Z + i·60 s (NY 06:55 → 07:06)."""
    base = datetime(2026, 1, 15, 11, 55, tzinfo=timezone.utc)
    algos = ("hop", "am_gate", "burst")
    vibs = ("none", "physical", "acoustic", "infra_felt")
    out: list[dict[str, Any]] = []
    for i in range(12):
        out.append(
            {
                "schemaVersion": SCHEMA_VERSION,
                "deviceId": node,
                "ts": to_wire_ts(datetime.fromtimestamp(base.timestamp() + 60 * i, timezone.utc)),
                "algo": algos[i % 3],
                "peakHz": 19500 + 100 * i,
                "suddenFreq": i in (1, 4, 7),
                "suddenState": "rotate" if i in (1, 4, 7) else "idle",
                "absA": round(0.10 + 0.01 * i, 3),
                "micEnergy": round(0.03 + 0.001 * i, 4),
                "vibClass": vibs[i % 4],
                "fMin": 15 if i in (10, 11) else 17000,
                "fMax": 20 if i in (10, 11) else 23000,
                "holdManual": i in (6, 7, 8),
            }
        )
    return out


def demo_fixture(node: str = "node1") -> list[dict[str, Any]]:
    """12 ``fleet_log`` records built from :func:`demo_telemetry` (warn/hold_refuse when held)."""
    recs = []
    for t in demo_telemetry(node):
        if t["holdManual"]:
            recs.append(log_record("warn", "hold_refuse", t, msg="holdManual — refuse patch"))
        else:
            recs.append(log_record("info", "ingest", t))
    return recs


def _demo(node: str) -> dict[str, Any]:
    os.environ.setdefault("IOT_ASP_AUTOROUTE_DRY_RUN", "1")
    gcs_io.DRY_RUN = True  # type: ignore[attr-defined]
    records = demo_fixture(node)
    written = [write_log_record(node, r) for r in records]
    return {
        "sample": records[0],
        "aggregate": aggregate_records(records, window_s=300, node=node),
        "written": sum(1 for w in written if w.get("ok")),
        "path": written[0].get("path") if written else None,
        "retention": {k: retention_plan()[k]["days"] for k in ("raw", "aggregates")},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m iot_asp_autoroute.fleet_log")
    parser.add_argument("--demo", action="store_true", help="offline: enriched sample + aggregate")
    parser.add_argument("--node", default="node1")
    args = parser.parse_args(argv)
    if not args.demo:
        parser.print_usage(sys.stderr)
        return 2
    print(json.dumps(_demo(args.node), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
