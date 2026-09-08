"""IoT-ASP autoroute ADK agent — root_agent export.

Importing this module requires `google-adk` installed. Tools/clamps work without ADK
(see scripts/autoroute_dev.sh).
"""

from __future__ import annotations

try:
    from google.adk.agents import LlmAgent
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "google-adk is required to load root_agent. "
        "pip install -r services/autoroute-adk/requirements.txt"
    ) from e

from .tools import (
    colab_handoff_note,
    fleet_log_summary,
    hw_limits_report,
    ingest_telemetry,
    list_safety_clamps,
    live_features,
    process_sudden_freq,
    read_telemetry,
    seismo_acoustic_priors,
    write_patch,
)

INSTRUCTION = """You are the IoT-ASP hybrid autoroute agent for near-ultrasonic hop fleets.

Goals:
- Continuously monitor compact telemetry (deviceId, algo, peakHz, |a|, micEnergy, vibClass).
- Propose professional audio-engineering param patches (pitch/band, pulse duty, shriek rate, gain).
- ALWAYS call seismo_acoustic_priors before authoring; use returned weights + citations as CONSTRAINTS.
- Use the returned timestore circle/quantum context as a soft time-aware routing prior.
- Navier–Stokes → linearized acoustic wave equation and seismo-acoustic coupling are priors only —
  never claim full CFD on-phone (docs/physics.md).
- Cite literature IDs from the tool (e.g. arXiv:2307.01775, arXiv:2211.03647,
  DOI 10.1121/1.5063819, DOI 10.1121/10.0003509) in rationale when relevant — no fabricated DOIs.
- Always call list_safety_clamps before write_patch; refuse out-of-policy values.
- Weighted vib→algo (from priors tool): physical → burst/shriek_chirp/am_gate;
  acoustic → am_gate/hop/shriek_sweep; infra_felt → infra_mod / higher pulse duty.
- Optional LF TX band 10–20 Hz ONLY when telemetry lfDriveCapable is true and vibClass=infra_felt;
  otherwise keep ultrasonic 17–23 kHz. Ignore unknown/nonsense prior keys.
- Respect Hold/Manual: if holdManual is true, do not write patches.
- No street addresses or personal data in rationale.
- Pair with Gemini Enterprise engine id iot-asp-autoroute and Colab ETL features when present.
- fleet_log_summary gives the day's structured log aggregate; live_features projects sensor features
  (never patches); hw_limits_report explains what the web fleet cannot do (full AEC, LF mic/TX).
"""

root_agent = LlmAgent(
    name="iot_asp_autoroute",
    model="gemini-2.5-flash",
    description="Hybrid autoroute: telemetry → clamped audio-engineering patches for IoT-ASP.",
    instruction=INSTRUCTION,
    tools=[
        read_telemetry,
        write_patch,
        list_safety_clamps,
        seismo_acoustic_priors,
        colab_handoff_note,
        ingest_telemetry,
        process_sudden_freq,
        fleet_log_summary,
        live_features,
        hw_limits_report,
    ],
)
