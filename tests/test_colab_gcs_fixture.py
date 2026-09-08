"""Golden dry-run fixture for #26 — no network, no secrets."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "fixtures" / "colab_gcs" / "features_node1_seed26.json"
SCRIPT = ROOT / "scripts" / "colab_gcs_fixture.sh"
ETL_DRY = ROOT / "scripts" / "colab_etl_dry_run.py"


def test_golden_features_shape():
    feat = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert feat["writer"] == "iot_asp_autoroute.features_live"
    assert feat["schemaVersion"] == 1
    assert feat["kind"] == "iot_asp_features"
    assert feat["sourceCount"] == 12
    assert feat["micDiffAlpha"] == 0.85
    assert isinstance(feat["sensorColumns"], list) and len(feat["sensorColumns"]) == 18
    assert "patches" not in json.dumps(feat).lower() or "never" in str(feat.get("credentialPolicy", "")).lower()


def test_colab_gcs_fixture_check(tmp_path, monkeypatch):
    monkeypatch.setenv("IOT_ASP_AUTOROUTE_DRY_ROOT", str(tmp_path))
    proc = subprocess.run(
        ["bash", str(SCRIPT), "--check"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OK fixture check" in proc.stdout


def test_colab_etl_dry_run_offline():
    proc = subprocess.run(
        [sys.executable, str(ETL_DRY)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data.get("ok") is True
    assert data.get("featureColumnCount", 0) > 0
    blob = proc.stdout.lower()
    for bad in ("begin private", "gcp_sa_json=", "api_key=", "sk-"):
        assert bad not in blob


def test_colab_gcs_fixture_refuses_live_gcs(tmp_path, monkeypatch):
    monkeypatch.setenv("IOT_ASP_AUTOROUTE_DRY_ROOT", str(tmp_path))
    monkeypatch.setenv("LIVE_GCS", "1")
    proc = subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    assert "Refusing" in proc.stderr or "Refusing" in proc.stdout
