"""#61 — Cloud Run ingest_app dry-run surface (no live GCS / no secrets)."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

ADK = Path(__file__).resolve().parents[1] / "services" / "autoroute-adk"
if str(ADK) not in sys.path:
    sys.path.insert(0, str(ADK))


@pytest.fixture()
def ingest_client(tmp_path, monkeypatch):
    monkeypatch.setenv("IOT_ASP_AUTOROUTE_DRY_RUN", "1")
    monkeypatch.setenv("IOT_ASP_AUTOROUTE_DRY_ROOT", str(tmp_path))
    monkeypatch.setenv("IOT_ASP_GCS_BUCKET", "")
    monkeypatch.setenv("IOT_ASP_AUTOROUTE_ON_INGEST", "0")
    for mod in (
        "iot_asp_autoroute.gcs_io",
        "iot_asp_autoroute.tools",
        "iot_asp_autoroute.fleet_log",
        "ingest_app",
    ):
        sys.modules.pop(mod, None)
    import iot_asp_autoroute.gcs_io as gcs_io

    importlib.reload(gcs_io)
    import ingest_app

    importlib.reload(ingest_app)
    ingest_app.app.config["TESTING"] = True
    return ingest_app.app.test_client(), tmp_path


def test_healthz(ingest_client) -> None:
    client, _ = ingest_client
    resp = client.get("/healthz")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert body["service"] == "iot-asp-ingest"


def test_patch_fallback_mock(ingest_client) -> None:
    client, _ = ingest_client
    resp = client.get("/patch.json?node=node1")
    assert resp.status_code == 200
    assert resp.headers.get("Cache-Control") == "no-store"
    data = resp.get_json()
    assert data["schemaVersion"] == 1
    assert data.get("engineId") == "iot-asp-autoroute"


def test_ingest_writes_telemetry(ingest_client) -> None:
    client, root = ingest_client
    payload = {
        "schemaVersion": 1,
        "deviceId": "node1",
        "ts": "2026-09-08T07:10:00Z",
        "seed": 7,
        "algo": "hop",
        "peakHz": 19000,
        "suddenFreq": False,
        "holdManual": False,
        "absA": 0.02,
        "micEnergy": -55,
        "band": "17-23k",
        "power": "ac120",
    }
    resp = client.post("/ingest", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get("ok") is True
    tel_dir = root / "meta" / "telemetry" / "node1"
    assert tel_dir.is_dir()
    assert any(tel_dir.glob("*.json"))


def test_default_dry_root_container_depth() -> None:
    """Cloud Run copies package to /app/iot_asp_autoroute — parents[3] must not crash."""
    import iot_asp_autoroute.gcs_io as gcs_io

    shallow = Path("/app/iot_asp_autoroute/gcs_io.py")
    with pytest.raises(IndexError):
        _ = shallow.parents[3]
    # Production helper must return a usable Path on the real checkout.
    assert isinstance(gcs_io._default_dry_root(), Path)
    assert gcs_io._default_dry_root().name in {".autoroute-dry", "iot-asp-autoroute-dry"}
