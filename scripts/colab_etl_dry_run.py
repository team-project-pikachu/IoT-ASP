#!/usr/bin/env python3
"""Offline dry-run for Colab ETL shared module (no GCS / Vertex / secrets)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_ADK = _ROOT / "services" / "autoroute-adk"
if str(_ADK) not in sys.path:
    sys.path.insert(0, str(_ADK))

from iot_asp_autoroute.colab_etl import (  # noqa: E402
    TELEMETRY_FEATURE_COLUMNS,
    offline_dry_run,
)
from iot_asp_autoroute.vib_anomaly import VIB_QUANTUM  # noqa: E402


def main() -> int:
    result = offline_dry_run()
    # Compact summary for evidence (full features nested)
    summary = {
        "ok": result["ok"],
        "missingTelemetryColumns": result["missingTelemetryColumns"],
        "sensorMissingColumns": result.get("sensorMissingColumns"),
        "featureColumnCount": result["featureColumnCount"],
        "sensorFeatureColumnCount": result.get("sensorFeatureColumnCount"),
        "telemetryFeatureColumnsDeclared": list(TELEMETRY_FEATURE_COLUMNS),
        "vibQuantumG": VIB_QUANTUM,
        "sampleHz": result["sampleHz"],
        "anomalyDisturbance": result["anomalyDisturbance"],
        "anomalyFunctions": result["anomalyFunctions"],
        "sharedModule": result["sharedModule"],
        "suggestionAlgo": result["suggestionAlgo"],
        "sensorSuggestionAlgo": result.get("sensorSuggestionAlgo"),
        "sensorShriekBias": result.get("sensorShriekBias"),
        "sensorBandBurst": result.get("sensorBandBurst"),
        "sensorMicDiff": result.get("sensorMicDiff"),
        "holdManualRefused": result["holdManualRefused"],
        "credentialPolicy": result["features"].get("credentialPolicy"),
        "priorHint": result["features"]["derived"]["priorHint"],
        "sensorPriorHint": result.get("sensorFeatures", {})
        .get("derived", {})
        .get("priorHint"),
    }
    print(json.dumps(summary, indent=2))
    print(
        f"\n# colab_etl dry-run ok={result['ok']} "
        f"disturbance={result['anomalyDisturbance']} "
        f"holdRefused={result['holdManualRefused']} quantum={VIB_QUANTUM}",
        file=sys.stderr,
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
