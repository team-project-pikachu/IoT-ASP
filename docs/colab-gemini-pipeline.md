# Colab ↔ Gemini Enterprise ↔ ADK pipeline

Offload heavy ETL to **Google Colab** (paid tier; account per `google-colab-etl` skill). Pair with **Gemini Enterprise (5 seats)** and the **ADK autoroute agent**.

## Flow

```
phones (telemetry + optional .webm)
    → private GCS (project bear-iot-asp-rec)
    → Colab ETL (spectra, vib features, NS/seismo priors as features — not CFD)
    → Gemini Enterprise (engine iot-asp-autoroute) interpretation / synthesis
    → ADK agent validates clamps + writes meta/patches/<nodeId>.json
    → nodes poll patches; study notes stay private
```

## Starter notebook

`notebooks/iot_asp_colab_etl.ipynb` — public stub:

- Auth via Colab `userdata.get('GCP_SA_JSON')` only (never download SA JSON to Studio/Laptop).
- Reads telemetry objects under `meta/telemetry/` (bucket name from userdata / env).
- Computes STFT peaks, accel LF energy, vib class heuristic.
- Writes feature JSON to `meta/features/`.
- Optional: invoke ADK / Vertex generateContent for patch **suggestion** (still clamped by worker).

## Env / secrets

| Name | Where | Notes |
|------|-------|--------|
| `GCP_SA_JSON` | Colab userdata only | Forbidden in git/chat |
| `GOOGLE_CLOUD_PROJECT` | `bear-iot-asp-rec` | |
| `IOT_ASP_GEMINI_ENGINE_ID` | `iot-asp-autoroute` | Discovery Engine app |
| `IOT_ASP_GCS_BUCKET` | private | set in userdata |

## Related

- [gemini-enterprise.md](gemini-enterprise.md)  
- [adk-autoroute.md](adk-autoroute.md)  
- [physics.md](physics.md)  
- Skill: `~/.cursor/skills/google-colab-etl/SKILL.md`
