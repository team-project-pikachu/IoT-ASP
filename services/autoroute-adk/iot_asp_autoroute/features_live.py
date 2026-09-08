"""Live / dry-run sensor features: accel · gyro · micDiff telemetry → ``meta/features``.

Issue #26. Extends (imports, never modifies) ``colab_etl`` and ``vib_anomaly``:

* ``SENSOR_COLUMNS`` are the additive ``schemaVersion: 1`` heartbeat keys from
  ``docs/api-contract.md`` (``ax..gz``, ``accelAxes``, ``gyroAxes``, ``outLevel``,
  ``micDiff``, ``bandBurst``, ``soundBurst``, ``extremeActive``, ``lfEnergy``,
  ``usEnergy``, watchdog counters).
* ``run_live`` reads the last ``limit`` telemetry points for a node (``*.json``
  objects **and** ``*.jsonl`` files), builds one features record via
  ``colab_etl.extract_features`` (SciPy vib anomaly over the 1 Hz ``absA`` series)
  and writes **only** ``meta/features/<node>/<ts>.json``.

Hard guard: this module never writes ``meta/patches/`` (Colab / ETL output is never
authoritative — the ADK worker clamps and writes patches). ``assert_not_patch_path``
raises before every write.

Secrets by **name** only: ``LIVE_GCS``, ``IOT_ASP_GCS_BUCKET``, ``GCP_SA_JSON``,
``GOOGLE_CLOUD_PROJECT``. Values are never printed or written into features.

Physics honesty: ``lfEnergy`` is a felt-proxy band energy (not infrasound capture),
``bandBurst`` thresholds are heuristic labels, ``micDiff`` is best-effort AEC
(``micEnergy − 0.85·outLevel``) — the browser cannot do full echo cancellation.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

# Allow ``python3 -m iot_asp_autoroute.features_live`` from services/autoroute-adk
_PKG = Path(__file__).resolve().parent
_ROOT = _PKG.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from iot_asp_autoroute import gcs_io  # noqa: E402
from iot_asp_autoroute.clamps import SCHEMA_VERSION  # noqa: E402
from iot_asp_autoroute.colab_etl import (  # noqa: E402
    SAMPLE_HZ,
    TELEMETRY_FEATURE_COLUMNS,
    extract_features,
    normalize_telemetry,
)
from iot_asp_autoroute.vib_anomaly import synthetic_demo_series  # noqa: E402

# ── constants (docs/specs/26-colab-live-gcs-features.md) ─────────────────────

SENSOR_COLUMNS: tuple[str, ...] = (
    "ax",
    "ay",
    "az",
    "gx",
    "gy",
    "gz",
    "accelAxes",
    "gyroAxes",
    "outLevel",
    "micDiff",
    "bandBurst",
    "soundBurst",
    "extremeActive",
    "lfEnergy",
    "usEnergy",
    "lastHopAgeMs",
    "ctxResumes",
    "watchdogTrips",
)
ALL_COLUMNS: tuple[str, ...] = TELEMETRY_FEATURE_COLUMNS + SENSOR_COLUMNS

MIC_DIFF_ALPHA = 0.85
BAND_LF_THR_DB = -60.0
BAND_US_THR_DB = -55.0
SHRIEK_MIC_DIFF_DB = 6.0
FEATURES_PREFIX = "meta/features/"
TELEMETRY_PREFIX = "meta/telemetry/"
FORBIDDEN_PREFIX = "meta/patches"
WRITER = "iot_asp_autoroute.features_live"
TS_FMT = "%Y-%m-%dT%H:%M:%SZ"

BAND_BURST_ALLOWED = frozenset({"lf", "us", "both"})
_BOOL_COLUMNS = frozenset({"soundBurst", "extremeActive"})
_INT_COLUMNS = frozenset({"lastHopAgeMs", "ctxResumes", "watchdogTrips"})
_AXES_COLUMNS = frozenset({"accelAxes", "gyroAxes"})
_ACCEL_SCALARS = ("ax", "ay", "az")
_GYRO_SCALARS = ("gx", "gy", "gz")

# ── pure helpers ─────────────────────────────────────────────────────────────


def _as_float(v: Any) -> float | None:
    """Finite float or None (bools are not numbers here)."""
    if v is None or isinstance(v, bool):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _as_bool(v: Any) -> bool | None:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return bool(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("true", "1", "yes", "on"):
            return True
        if s in ("false", "0", "no", "off", ""):
            return False
    return None


def _as_axes(v: Any) -> list[float] | None:
    if isinstance(v, (str, bytes, dict)) or v is None:
        return None
    try:
        items = list(v)
    except TypeError:
        return None
    if len(items) != 3:
        return None
    out = [_as_float(x) for x in items]
    if any(x is None for x in out):
        return None
    return [float(x) for x in out]  # type: ignore[arg-type]


def mic_diff(
    mic_energy: Any,
    out_level: Any,
    alpha: float = MIC_DIFF_ALPHA,
    given: Any = None,
) -> float:
    """Best-effort AEC residual ``micEnergy − alpha·outLevel`` (dB).

    A phone-supplied ``micDiff`` (``given``) wins **unchanged** when it is a finite
    number. Non-numeric / ``None`` inputs coerce to ``0.0``. Rounded to 3 dp.
    """
    g = _as_float(given)
    if g is not None:
        return g
    mic = _as_float(mic_energy) or 0.0
    out = _as_float(out_level) or 0.0
    return round(float(mic) - float(alpha) * float(out), 3)


def band_burst(
    lf_energy: Any,
    us_energy: Any,
    lf_thr: float = BAND_LF_THR_DB,
    us_thr: float = BAND_US_THR_DB,
) -> str | None:
    """Classify a band burst: ``'lf'`` | ``'us'`` | ``'both'`` | ``None``.

    Heuristic labels only (not infrasound capture): LF ≥ ``lf_thr`` dB, US ≥ ``us_thr`` dB.
    """
    lf = _as_float(lf_energy)
    us = _as_float(us_energy)
    lf_hit = lf is not None and lf >= float(lf_thr)
    us_hit = us is not None and us >= float(us_thr)
    if lf_hit and us_hit:
        return "both"
    if lf_hit:
        return "lf"
    if us_hit:
        return "us"
    return None


def project_sensor_features(t: dict[str, Any]) -> dict[str, Any]:
    """Return only the ``SENSOR_COLUMNS`` present in ``t``, numeric-coerced.

    * scalars → ``float``; ``soundBurst`` / ``extremeActive`` → ``bool``;
      ``lastHopAgeMs`` / ``ctxResumes`` / ``watchdogTrips`` → ``int``;
    * ``bandBurst`` kept only when in ``{'lf','us','both'}``;
    * ``accelAxes`` / ``gyroAxes`` must be 3 numbers → ``list[float]`` (else dropped),
      and are synthesised from ``ax,ay,az`` / ``gx,gy,gz`` when absent;
    * ``None`` values and unknown keys are ignored.
    """
    out: dict[str, Any] = {}
    for key in SENSOR_COLUMNS:
        if key not in t or t[key] is None:
            continue
        v = t[key]
        if key in _AXES_COLUMNS:
            axes = _as_axes(v)
            if axes is not None:
                out[key] = axes
        elif key in _BOOL_COLUMNS:
            b = _as_bool(v)
            if b is not None:
                out[key] = b
        elif key in _INT_COLUMNS:
            f = _as_float(v)
            if f is not None:
                out[key] = int(round(f))
        elif key == "bandBurst":
            s = str(v).strip().lower()
            if s in BAND_BURST_ALLOWED:
                out[key] = s
        else:
            f = _as_float(v)
            if f is not None:
                out[key] = float(f)

    if "accelAxes" not in out and all(k in out for k in _ACCEL_SCALARS):
        out["accelAxes"] = [out[k] for k in _ACCEL_SCALARS]
    if "gyroAxes" not in out and all(k in out for k in _GYRO_SCALARS):
        out["gyroAxes"] = [out[k] for k in _GYRO_SCALARS]
    return out


def normalize_ts(ts: Any) -> str | None:
    """ISO-8601 (``%Y-%m-%dT%H:%M:%SZ``) from ISO strings or epoch seconds / ms."""
    if ts is None:
        return None
    if isinstance(ts, bool):
        return None
    if isinstance(ts, (int, float)):
        if not math.isfinite(float(ts)):
            return None
        secs = float(ts) / 1000.0 if float(ts) > 1e12 else float(ts)
        try:
            return datetime.fromtimestamp(secs, tz=timezone.utc).strftime(TS_FMT)
        except (OverflowError, OSError, ValueError):
            return None
    s = str(ts).strip()
    if not s:
        return None
    if s.isdigit():
        return normalize_ts(int(s))
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        # Object-name style "2026-09-08T00-00-05Z" (colons replaced by dashes)
        try:
            dt = datetime.strptime(s, "%Y-%m-%dT%H-%M-%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            return s
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime(TS_FMT)


# ── reading telemetry (objects + jsonl) ───────────────────────────────────────


def _read_text(object_name: str) -> str | None:
    """Text of an object (dry-run mirror or GCS). Only used for ``*.jsonl``."""
    if gcs_io.is_dry_run():
        path = gcs_io.DRY_ROOT / object_name
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8")
    from google.cloud import storage  # type: ignore

    client = storage.Client(project=gcs_io.PROJECT)
    blob = client.bucket(gcs_io.BUCKET).blob(object_name)
    if not blob.exists():
        return None
    return blob.download_as_text()


def _normalize_point(raw: Any, name: str) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    t = normalize_telemetry(raw)
    ts = normalize_ts(t.get("ts", t.get("t")))
    if ts is None:
        # Fall back to the object name stem (ingest names objects by ts with ':'→'-')
        ts = normalize_ts(Path(name).stem) or ""
    t["ts"] = ts
    t["_source"] = name
    return t


def parse_telemetry_objects(
    names: list[str],
    reader: Callable[[str], dict[str, Any] | None] | None = None,
    text_reader: Callable[[str], str | None] | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Load telemetry points from object names under ``meta/telemetry/<node>/``.

    ``*.json`` → one point; ``*.jsonl`` → one point per non-blank line (bad lines
    skipped and appended to ``errors`` when given). Every point is normalised
    (``colab_etl.normalize_telemetry``), ``ts`` coerced to ISO-8601, and the result
    is sorted by ``ts`` ascending (stable on object name, then line index).
    """
    read_json = reader or gcs_io.read_json
    read_text = text_reader or _read_text
    points: list[tuple[str, str, int, dict[str, Any]]] = []
    for name in names:
        lower = name.lower()
        if lower.endswith(".jsonl"):
            text = read_text(name)
            if text is None:
                continue
            for idx, line in enumerate(text.splitlines()):
                if not line.strip():
                    continue
                try:
                    raw = json.loads(line)
                except json.JSONDecodeError as exc:
                    if errors is not None:
                        errors.append({"object": name, "line": idx, "error": str(exc)})
                    continue
                p = _normalize_point(raw, name)
                if p is None:
                    if errors is not None:
                        errors.append({"object": name, "line": idx, "error": "not an object"})
                    continue
                points.append((p["ts"], name, idx, p))
        elif lower.endswith(".json"):
            try:
                raw = read_json(name)
            except (OSError, ValueError) as exc:
                if errors is not None:
                    errors.append({"object": name, "line": 0, "error": str(exc)})
                continue
            p = _normalize_point(raw, name)
            if p is None:
                if errors is not None:
                    errors.append({"object": name, "line": 0, "error": "not an object"})
                continue
            points.append((p["ts"], name, 0, p))
    points.sort(key=lambda item: (item[0], item[1], item[2]))
    return [item[3] for item in points]


def list_telemetry_names(node: str) -> list[str]:
    """Object names under ``meta/telemetry/<node>/`` — ``*.json`` **and** ``*.jsonl``.

    ``gcs_io.list_prefix`` dry-run globs only ``*.json``; live ``list_blobs`` already
    returns both, so the extra ``*.jsonl`` glob is dry-run only.
    """
    prefix = f"{TELEMETRY_PREFIX}{node}/"
    names = list(gcs_io.list_prefix(prefix))
    if gcs_io.is_dry_run():
        root = gcs_io.DRY_ROOT / prefix
        if root.exists():
            names.extend(
                str(p.relative_to(gcs_io.DRY_ROOT)) for p in root.rglob("*.jsonl") if p.is_file()
            )
    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return sorted(out)


def latest_points(node: str, limit: int = 200) -> list[dict[str, Any]]:
    """Last ``limit`` telemetry points for ``node`` sorted by ``ts`` ascending."""
    names = list_telemetry_names(node)
    points = parse_telemetry_objects(names)
    lim = max(1, int(limit))
    return points[-lim:]


# ── feature record ───────────────────────────────────────────────────────────


def _vib_series(points: list[dict[str, Any]]) -> list[float]:
    series: list[float] = []
    for p in points:
        v = p.get("absA", p.get("a"))
        f = _as_float(v)
        if f is not None:
            series.append(float(f))
    return series


def shriek_bias(sensors: dict[str, Any], mic_diff_db: float = SHRIEK_MIC_DIFF_DB) -> bool:
    """``soundBurst ∨ extremeActive ∨ micDiff > 6 dB`` — a hint, never a patch."""
    if sensors.get("soundBurst") is True or sensors.get("extremeActive") is True:
        return True
    md = _as_float(sensors.get("micDiff"))
    return md is not None and md > float(mic_diff_db)


def build_feature_record(points: list[dict[str, Any]], node: str) -> dict[str, Any]:
    """Features record for the latest point + 1 Hz vib series over all points.

    Additive over ``colab_etl.extract_features``: ``sensors``, ``shriekBias``,
    ``sourceCount``, ``live`` (default ``False``; ``run_live`` sets it),
    ``sensorColumns``, ``micDiffAlpha``, ``writer``.
    """
    if not points:
        raise ValueError("build_feature_record: points must be non-empty")
    latest = dict(points[-1])
    latest.pop("_source", None)
    latest.setdefault("deviceId", node)
    series = _vib_series(points)
    record = extract_features(latest, vib_series=series)

    sensors = project_sensor_features(latest)
    if "micDiff" not in sensors:
        mic = _as_float(latest.get("micEnergy"))
        out = _as_float(latest.get("outLevel"))
        if mic is not None and out is not None:
            sensors["micDiff"] = mic_diff(mic, out)
    if "bandBurst" not in sensors:
        bb = band_burst(latest.get("lfEnergy"), latest.get("usEnergy"))
        if bb is not None:
            sensors["bandBurst"] = bb

    record["schemaVersion"] = SCHEMA_VERSION
    record["kind"] = "iot_asp_features"
    record["deviceId"] = str(latest.get("deviceId") or node)
    record["sensors"] = sensors
    record["shriekBias"] = shriek_bias(sensors)
    record["sourceCount"] = len(points)
    record["live"] = False
    record["sensorColumns"] = list(SENSOR_COLUMNS)
    record["micDiffAlpha"] = MIC_DIFF_ALPHA
    record["sampleHz"] = SAMPLE_HZ
    record["writer"] = WRITER
    record["sourceObjects"] = sorted({str(p.get("_source")) for p in points if p.get("_source")})
    return record


def features_object_name(node: str, ts: str) -> str:
    return f"{FEATURES_PREFIX}{node}/{str(ts).replace(':', '-')}.json"


def assert_not_patch_path(object_name: str) -> None:
    """Hard guard: this module never writes ``meta/patches``."""
    if str(object_name).lstrip("/").startswith(FORBIDDEN_PREFIX):
        raise ValueError("refuse: features_live never writes meta/patches")


# ── live gate + run ──────────────────────────────────────────────────────────


def env_live_gate() -> bool:
    """``LIVE_GCS == "1"`` **and** a non-empty ``IOT_ASP_GCS_BUCKET`` (names only)."""
    return os.environ.get("LIVE_GCS") == "1" and bool(os.environ.get("IOT_ASP_GCS_BUCKET"))


@contextmanager
def _gcs_mode(live: bool) -> Iterator[None]:
    """Force ``gcs_io`` to the dry-run mirror (``live=False``) or to GCS (``live=True``)
    for the duration; the previous state is restored afterwards."""
    prev_dry = gcs_io.DRY_RUN
    prev_bucket = gcs_io.BUCKET
    try:
        if live:
            gcs_io.DRY_RUN = False
            gcs_io.BUCKET = os.environ.get("IOT_ASP_GCS_BUCKET") or prev_bucket
        else:
            gcs_io.DRY_RUN = True
        yield
    finally:
        gcs_io.DRY_RUN = prev_dry
        gcs_io.BUCKET = prev_bucket


def run_live(
    node: str,
    limit: int = 200,
    write: bool = True,
    live: bool | None = None,
) -> dict[str, Any]:
    """Read the last ``limit`` telemetry points and write one features object.

    ``live`` defaults to ``env_live_gate()``; an explicit ``True`` still requires a
    non-empty ``IOT_ASP_GCS_BUCKET`` (otherwise the run is downgraded to the dry-run
    mirror). Only ``meta/features/<node>/<ts>.json`` is ever written.
    """
    if live is None:
        is_live = env_live_gate()
    else:
        is_live = bool(live) and bool(os.environ.get("IOT_ASP_GCS_BUCKET"))
    node = str(node)
    with _gcs_mode(is_live):
        points = latest_points(node, limit)
        if not points:
            return {
                "ok": False,
                "error": f"no telemetry under {TELEMETRY_PREFIX}{node}/",
                "uri": None,
                "node": node,
                "live": is_live,
                "sourceCount": 0,
                "featureKeys": [],
                "object": None,
            }
        record = build_feature_record(points, node)
        record["live"] = is_live
        name = features_object_name(node, str(record["ts"]))
        assert_not_patch_path(name)
        if not name.startswith(FEATURES_PREFIX):
            raise ValueError("refuse: features_live writes only under meta/features/")
        uri: str | None = None
        if write:
            uri = gcs_io.write_json(name, record)
    return {
        "ok": True,
        "uri": uri,
        "node": node,
        "live": is_live,
        "sourceCount": len(points),
        "featureKeys": sorted(record.keys()),
        "object": name,
        "written": bool(write),
        "shriekBias": record["shriekBias"],
    }


# ── offline demo seed + CLI ──────────────────────────────────────────────────

DEMO_BASE_TS = "2026-09-08T00:00:00Z"


def demo_points(node: str = "node1", n: int = 12, seed: int = 26) -> list[dict[str, Any]]:
    """Deterministic synthetic heartbeats with sensor columns (no I/O)."""
    rng = random.Random(seed)
    vib = synthetic_demo_series(n, seed)
    base = datetime.strptime(DEMO_BASE_TS, TS_FMT).replace(tzinfo=timezone.utc)
    out: list[dict[str, Any]] = []
    for i in range(n):
        ts = datetime.fromtimestamp(base.timestamp() + i, tz=timezone.utc).strftime(TS_FMT)
        p: dict[str, Any] = {
            "schemaVersion": SCHEMA_VERSION,
            "deviceId": node,
            "ts": ts,
            "algo": "hop",
            "suddenFreq": False,
            "holdManual": False,
            "band": "17-23k",
            "vibClass": "physical",
            "absA": vib[i],
            "ax": round(rng.uniform(-0.05, 0.05), 4),
            "ay": round(rng.uniform(-0.05, 0.05), 4),
            "az": round(1.0 + rng.uniform(-0.02, 0.02), 4),
            "gx": round(rng.uniform(-0.5, 0.5), 4),
            "gy": round(rng.uniform(-0.5, 0.5), 4),
            "gz": round(rng.uniform(-0.5, 0.5), 4),
            "outLevel": -30.0,
            "micEnergy": -40.0,
            "lfEnergy": -70.0,
            "usEnergy": -50.0,
            "lastHopAgeMs": 400 + 10 * i,
            "ctxResumes": 0,
            "watchdogTrips": 0,
        }
        if i == 9:
            p["soundBurst"] = True
            p["micEnergy"] = -20.0
        out.append(p)
    return out


def _seed_demo(node: str = "node1", n: int = 12, seed: int = 26) -> list[str]:
    """Write ``n`` synthetic telemetry objects to the **dry-run mirror**; returns URIs."""
    uris: list[str] = []
    with _gcs_mode(False):
        for p in demo_points(node, n, seed):
            name = f"{TELEMETRY_PREFIX}{node}/{str(p['ts']).replace(':', '-')}.json"
            assert_not_patch_path(name)
            uris.append(gcs_io.write_json(name, p))
    return uris


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python3 -m iot_asp_autoroute.features_live",
        description="Telemetry sensors → meta/features/<node>/<ts>.json (never meta/patches).",
    )
    ap.add_argument("--node", default="node1")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--live", action="store_true", help="write to GCS (needs IOT_ASP_GCS_BUCKET)")
    ap.add_argument("--seed-demo", action="store_true", help="seed 12 synthetic points offline first")
    args = ap.parse_args(argv)

    seeded: list[str] = []
    if args.seed_demo:
        seeded = _seed_demo(args.node)
    res = run_live(args.node, args.limit, write=True, live=bool(args.live))
    res["seeded"] = len(seeded)
    if seeded:
        res["seedUris"] = [seeded[0], seeded[-1]]
    print(json.dumps(res, sort_keys=True))
    return 0 if res.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
