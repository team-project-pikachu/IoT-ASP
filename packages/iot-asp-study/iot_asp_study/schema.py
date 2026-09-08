"""Public-safe session sidecar schema (opaque codes only — no street addresses)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

REQUIRED_SIDECAR_KEYS = (
    "ext_source",
    "site_code",
    "node",
    "algo",
    "vib_channel",
    "started_at_utc",
    "ended_at_utc",
)

# Public vocabulary. Private study may use opaque site codes in ext_source/site_code;
# those must stay out of the public default branch.
NODES = frozenset({"node1", "node2", "node3"})
ALGOS = frozenset(
    {
        "hop",
        "am_gate",
        "shriek_chirp",
        "shriek_sweep",
        "burst",
        "infra_mod",
        "other",
    }
)
VIB_CHANNELS = frozenset({"physical", "acoustic", "infra_felt", "none", "mixed"})
# Prefer these public tokens; opaque private codes are allowed as non-empty strings
# but doctor/scrub will reject patterns that look like street addresses in *public* files.
EXT_SOURCE_PUBLIC = frozenset({"neighbor_unit", "outside", "none"})


def _parse_utc(label: str, val: Any) -> tuple[datetime | None, str]:
    if not isinstance(val, str) or not val.strip():
        return None, f"{label} must be a non-empty ISO-8601 string"
    raw = val.strip()
    # Accept trailing Z or explicit offset; require timezone-aware UTC fields.
    try:
        if raw.endswith("Z"):
            dt = datetime.fromisoformat(raw[:-1] + "+00:00")
        else:
            dt = datetime.fromisoformat(raw)
    except ValueError:
        return None, f"{label} must be ISO-8601 (got {raw!r})"
    if dt.tzinfo is None:
        return None, f"{label} must be timezone-aware UTC (Z or offset)"
    return dt.astimezone(timezone.utc), "ok"


def validate_sidecar(payload: dict[str, Any]) -> tuple[bool, str]:
    """Validate a recording/session sidecar dict. Returns (ok, message)."""
    if not isinstance(payload, dict):
        return False, "sidecar must be an object"
    missing = [k for k in REQUIRED_SIDECAR_KEYS if k not in payload]
    if missing:
        return False, f"missing keys: {', '.join(missing)}"

    node = payload.get("node")
    if node not in NODES:
        return False, f"node must be one of {sorted(NODES)}"

    algo = payload.get("algo")
    if algo not in ALGOS:
        return False, f"algo must be one of {sorted(ALGOS)}"

    vib = payload.get("vib_channel")
    if vib not in VIB_CHANNELS:
        return False, f"vib_channel must be one of {sorted(VIB_CHANNELS)}"

    started, err = _parse_utc("started_at_utc", payload.get("started_at_utc"))
    if started is None:
        return False, err
    ended, err = _parse_utc("ended_at_utc", payload.get("ended_at_utc"))
    if ended is None:
        return False, err
    if ended < started:
        return False, "ended_at_utc must be >= started_at_utc"

    site = payload.get("site_code")
    if not isinstance(site, str) or not site.strip():
        return False, "site_code must be a non-empty opaque string"

    ext = payload.get("ext_source")
    if not isinstance(ext, str) or not ext.strip():
        return False, "ext_source must be a non-empty string"
    # Encourage public tokens; still accept opaque private codes for local validation.
    _ = EXT_SOURCE_PUBLIC

    return True, "ok"
