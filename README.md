# IoT-ASP — Adaptive Signal Processing

Near-ultrasonic **hop fleet** for three iPhones, each blasting through its own Soundcore 2 speaker.

## Live app

Public blaster (Vercel): **https://hop-ultrasonic-1digital-design.vercel.app/**  
(Source mirror also lives under `public/` in this repo.)

## Constraints

- **C1:** Phone → speaker = **iOS native Bluetooth A2DP** only (not Web Bluetooth). See `docs/DESIGN_CONSTRAINTS.md`, `docs/iphone-bluetooth.md`.
- **C2:** Future Raspberry Pi field node uses **USB-C** (GitHub #14) — not MVP web.

## Fleet setup

1. Open the live URL on all three phones (2× iPhone 16 + 1× iPhone 14).
2. Pair **1 iPhone ↔ 1 Soundcore 2** in **Settings → Bluetooth**; route via **Control Center** (system A2DP).
3. Mode = **Blaster / TX** on every phone → tap **Signal on**.
4. Hops are **incoherent** (independent per Safari tab; no shared seed).
5. Control loop: **sudden frequency detect → Gemini/ADK autorotate** (`docs/autoroute.md`).

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

- **API contract** (telemetry + patch + `schemaVersion`): [`docs/api-contract.md`](docs/api-contract.md) — frontend polls/applies only; no Vertex keys in the browser
- Gemini Enterprise engine: **`iot-asp-autoroute`** (`docs/gemini-enterprise.md`)
- ADK agent: `services/autoroute-adk/` (`docs/adk-autoroute.md`) — deploy **independently** of Vercel; dry-run `bash scripts/autoroute_dev.sh`
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
