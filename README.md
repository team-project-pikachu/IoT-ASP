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

## Developer workflow

- **Project memory:** `CLAUDE.md` (invariants, commands) + path-scoped `.claude/rules/*.md`. Cursor rules in `.cursor/rules/*.mdc` convert deterministically with `python3 scripts/mdc_convert.py` (mapping table in `CLAUDE.md`; CI runs `--check`).
- **Feature specs:** `docs/specs/` — one per Project 5 issue; index in `docs/specs/README.md` and `SPEC.md`.
- **Local gates:** `make all` = `scripts/ci_static_gates.sh` + `scripts/autoroute_dev.sh` + `pytest tests` + `mdc_convert.py --check` (`pip install -r requirements-dev.txt` first).
- **CI:** `.github/workflows/ci.yml` (jobs `autoroute`, `static_gates`, `tests`, `mdc check`, `pr_issue_ref`). PRs must reference an issue.
- **Ship:** `.github/workflows/deploy.yml` — gates → **dev** (Vercel preview) → **test** (smoke) → **prod**; secrets by name only (`docs/deploy.md`, issue #27). Vercel's own Git auto-deploy is disabled in `vercel.json` so Actions owns deploys.
- **Main protection:** `.github/rulesets/main-protection.json` (import at Settings → Rules or `make protect-main`; `docs/branch-protection.md`).

## Layout

```
public/                 # shipped static web blaster (PWA)
docs/                   # gemini, ADK, autoroute, physics, Colab, deploy, branch protection
docs/specs/             # feature specs per Project 5 issue
services/autoroute-adk/ # Google ADK Python agent (+ fleet_log, features_live, mic_diff)
tests/                  # pytest + tests/e2e (Playwright smoke)
scripts/                # gates, dry-run, mdc_convert, deploy smoke, gh_protect_main
notebooks/              # Colab ETL stub
reference/knowledge-base/  # Context7 refreshable KB
reference/knowledge/    # Firecrawl ingest (incl. ADK)
.claude/                # Claude Code rules (path-scoped) + converted skills/manifest
.github/                # ci.yml, deploy.yml, rulesets/, PR template
CLAUDE.md               # project memory (Cursor .mdc converted blocks live here)
SPEC.md
Makefile
vercel.json
```
