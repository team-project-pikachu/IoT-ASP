#!/usr/bin/env python3
"""Doctor for packages/iot-asp-study — schema fixture + public-tree PII heuristics."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iot_asp_study.paths import resolve_study_root  # noqa: E402
from iot_asp_study.schema import validate_sidecar  # noqa: E402
from iot_asp_study.scrub import scan_paths  # noqa: E402


def main() -> int:
    example = ROOT / "templates" / "sidecar.example.json"
    payload = json.loads(example.read_text(encoding="utf-8"))
    ok, msg = validate_sidecar(payload)
    if not ok:
        print(f"FAIL schema: {msg}", file=sys.stderr)
        return 1
    print(f"OK schema fixture: {msg}")

    public_files = [
        ROOT / "README.md",
        ROOT / "PROVENANCE.md",
        ROOT / "templates" / "PROTOCOL.template.md",
        ROOT / "templates" / "sidecar.example.json",
        ROOT / "scripts" / "upload_recordings.sh",
    ]
    hits = scan_paths(public_files)
    if hits:
        print("FAIL PII markers in public package files:", file=sys.stderr)
        for path, kinds in hits.items():
            print(f"  {path}: {kinds}", file=sys.stderr)
        return 2
    print("OK public package scrub")

    study = resolve_study_root(ROOT.parents[1])  # IoT-ASP repo root
    if study:
        print(f"OK study root present (local/private): {study}")
    else:
        print("NOTE: no local study/ or IOT_ASP_STUDY_ROOT — expected for CI/public clones")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
