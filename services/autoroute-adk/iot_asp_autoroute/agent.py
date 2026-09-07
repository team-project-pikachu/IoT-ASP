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
    ingest_telemetry,
    list_safety_clamps,
    process_sudden_freq,
    read_telemetry,
    seismo_acoustic_priors,
    write_patch,
)

INSTRUCTION = """You are the IoT-ASP hybrid autoroute agent for near-ultrasonic hop fleets.

Goals:
- Continuously monitor compact telemetry (deviceId, algo, peakHz, |a|, micEnergy, vibClass).
- Propose professional audio-engineering param patches (pitch/band, pulse duty, shriek rate, gain).
- Use Navier–Stokes / linearized acoustic / seismo-acoustic priors as CONSTRAINTS only —
  never claim full CFD on-phone.
- Always call list_safety_clamps before write_patch; refuse out-of-policy values.
- Prefer structure-borne (physical) → burst/shriek_chirp/am_gate; acoustic → am_gate/hop/shriek_sweep;
  infra_felt → infra_mod / higher pulse duty.
- Respect Hold/Manual: if holdManual is true, do not write patches.
- No street addresses or personal data in rationale.
- Pair with Gemini Enterprise engine id iot-asp-autoroute and Colab ETL features when present.
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
    ],
)
