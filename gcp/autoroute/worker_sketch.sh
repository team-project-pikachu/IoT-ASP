#!/usr/bin/env bash
# Minimal GCP autoroute worker sketch (non-ADK fallback). Prefer services/autoroute-adk.
set -euo pipefail
export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-bear-iot-asp-rec}"
export GOOGLE_CLOUD_LOCATION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
export IOT_ASP_GEMINI_ENGINE_ID="${IOT_ASP_GEMINI_ENGINE_ID:-iot-asp-autoroute}"
echo "Use ADK path: docs/adk-autoroute.md"
echo "Dry-run: bash scripts/autoroute_dev.sh"
python3 - <<'PY'
# Vertex generateContent sketch — clamps still required before writing patches.
import os
print("project", os.environ["GOOGLE_CLOUD_PROJECT"])
print("engine", os.environ["IOT_ASP_GEMINI_ENGINE_ID"])
print("Prefer: from google import genai; client=genai.Client(vertexai=True, project=..., location=...)")
PY
