"""API contract alignment — HTML ↔ Python fleet_log ↔ docs/api-contract.md (#22 #11 #61).

Offline only. Never claims live ingest/patch URLs or HW lab results.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "services" / "autoroute-adk"
if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

from iot_asp_autoroute.fleet_log import RECORD_KEYS  # noqa: E402

HTML = (ROOT / "public" / "index.html").read_text(encoding="utf-8")
CONTRACT = (ROOT / "docs" / "api-contract.md").read_text(encoding="utf-8")

# schemaVersion:1 ★ fields from docs/api-contract.md (frontend must emit)
STAR_FIELDS = (
    "schemaVersion",
    "deviceId",
    "algo",
    "suddenFreq",
)

# Contract optional keys that Balanced stack already wires in telemetryPayload
WIRED_OPTIONAL = (
    "band",
    "power",
    "nightNY",
    "holdManual",
    "impulse",
    "volBlast",
    "alarmState",
    "ax",
    "ay",
    "az",
    "gx",
    "gy",
    "gz",
    "absOmega",
)


def _fleet_log_keys_from_html(html: str) -> list[str]:
    m = re.search(r"const FLEET_LOG_KEYS = \[([\s\S]*?)\];", html)
    assert m, "FLEET_LOG_KEYS missing"
    return re.findall(r'"([^"]+)"', m.group(1))


def test_fleet_log_keys_match_python_record_keys() -> None:
    keys = _fleet_log_keys_from_html(HTML)
    assert keys == RECORD_KEYS
    assert len(keys) == 24


def test_telemetry_payload_emits_star_and_wired_optional() -> None:
    assert HTML.count("function telemetryPayload(){") == 1
    body_start = HTML.index("function telemetryPayload(){")
    body = HTML[body_start : body_start + 3500]
    for tok in STAR_FIELDS + WIRED_OPTIONAL:
        assert tok in body, tok


def test_api_contract_doc_mentions_impulse_alarm_gyro() -> None:
    for tok in ("impulse", "volBlast", "alarmState", "gx", "gy", "gz", "schemaVersion: 1"):
        assert tok in CONTRACT, tok


def test_backend_url_constants_empty_by_default() -> None:
    """#61 — live URLs are query overrides; no baked secrets."""
    assert 'BACKEND_TELEMETRY_URL = ""' in HTML
    assert 'BACKEND_PATCH_URL = ""' in HTML
    assert "fleetBackendStrip" in HTML


def test_no_navigator_bluetooth_tx() -> None:
    assert "navigator.bluetooth" not in HTML
