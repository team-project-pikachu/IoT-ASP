# IoT-ASP — Adaptive Signal Processing

Near-ultrasonic **hop fleet** for three iPhones, each blasting through its own Soundcore 2 speaker.

## Live app

Public blaster (Vercel): **https://hop-ultrasonic-1digital-design.vercel.app/**  
(Source mirror also lives under `public/` in this repo.)

## Fleet setup

1. Open the live URL on all three phones (2× iPhone 16 + 1× iPhone 14).
2. Pair **1 iPhone ↔ 1 Soundcore 2** (Bluetooth / Control Center).
3. Mode = **Blaster / TX** on every phone → tap **Signal on**.
4. Hops are **incoherent** (independent per Safari tab; no shared seed).

See `SPEC.md` for Soundcore 2 manufacturer limits (12 W, BT 5.0, BassUp/DSP — expect near-ultrasonic roll-off).

## Vibration policy (parked — material-dependent)

The system should respond to vibration **physical or acoustic**, depending on materials/setup:

| Channel | Sensor path | Typical materials / setup |
|---------|-------------|---------------------------|
| **Physical** | Linear accelerometer / `DeviceMotionEvent` | Phone body, table mount, speaker enclosure contact |
| **Acoustic** | Mic + in-band spectrum energy | Air path, Soundcore cone/cabinet, room surfaces |
| **Selection** | Arm one or both based on setup | Phone-on-table → physical; BT radiate → acoustic; over-air listen → mic |

Docs ingest: `reference/knowledge/INGEST.md`.

## Roadmap

Tracked as GitHub milestones M0–M5 (seeds, monitoring, vib rotation, RLHF ±, SensorKit research). Parked features are issues labeled `parked`.

## Control plane

- Gemini Enterprise engine: **`iot-asp-autoroute`** (`docs/gemini-enterprise.md`)
- ADK agent: `services/autoroute-adk/` (`docs/adk-autoroute.md`) — https://docs.cloud.google.com/agent-builder/agent-development-kit/overview
- Colab ETL stub: `notebooks/iot_asp_colab_etl.ipynb`
- Knowledge base: `reference/knowledge-base/` + `bash scripts/kb_refresh.sh`
- Private study: local `study/` (gitignored)

## Layout

```
public/                 # shipped static web blaster (PWA)
docs/                   # gemini, ADK, autoroute, physics, Colab
services/autoroute-adk/ # Google ADK Python agent
notebooks/              # Colab ETL stub
reference/knowledge-base/  # Context7 refreshable KB
reference/knowledge/    # Firecrawl ingest (incl. ADK)
SPEC.md
vercel.json
```
