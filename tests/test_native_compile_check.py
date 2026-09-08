"""CLT-only native compile-check (#41) — no Xcode.app / SensorKit claim."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "native_compile_check.sh"


def test_native_compile_check_script():
    assert SCRIPT.is_file()
    proc = subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    # Exit 2 only if swift missing; otherwise must succeed without App Store claims.
    assert proc.returncode in (0, 2), proc.stdout + proc.stderr
    if proc.returncode == 0:
        assert "OK native_compile_check" in proc.stdout
        assert "alarm_smoke OK" in proc.stdout
        assert "IoTASPSmoke OK" in proc.stdout
        assert "App Store" in proc.stdout or "SensorKit" in proc.stdout
