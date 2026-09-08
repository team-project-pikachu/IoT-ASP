# IoT-ASP product roadmap (OS / surface)

Canonical product plan. **Milestones = OS/product surface.** **Labels = work category.**  
Legacy M0–M9 numbers are closed or renamed — do not open parallel taxonomies.

**Board:** [Project 5](https://github.com/orgs/team-project-pikachu/projects/5) · **Closed log:** [mvp-closed-log.md](mvp-closed-log.md)  
**PRD:** [PRD.md](PRD.md) · **UAT:** [UAT.md](UAT.md) · **Testing (SEBoK V&V):** [TESTING_PLAN.md](TESTING_PLAN.md) · **PWA architecture:** [architecture-pwa.md](architecture-pwa.md) · **Traceability:** [test-traceability.md](test-traceability.md)

### Issue title convention

`{Surface}: <short description>` — prefixes `iOS:` · `macOS:` · `Nest:` · `Sonos:` · `Platform:` / `ADK:` / `Agentic:`. Do not use `M0:`–`M9:` in new titles.

## Milestones (live)

| Surface | Milestone | URL |
|---------|-----------|-----|
| **iOS / iPhone** | Native app, SensorKit, CoreMotion, AVFoundation, on-device ultrasonic | https://github.com/team-project-pikachu/IoT-ASP/milestone/10 |
| **macOS / Mac Studio** | Desktop web hop blaster, fleet ops from Studio | https://github.com/team-project-pikachu/IoT-ASP/milestone/1 |
| **Google Home / Nest** | Home SDK, Nest cam, sound-burst alarm, glass shatter | https://github.com/team-project-pikachu/IoT-ASP/milestone/9 |
| **Sonos** | Beam Gen 2 route / DSP policy (secondary to Soundcore A2DP) | https://github.com/team-project-pikachu/IoT-ASP/milestone/12 |
| **Platform / Agentic / ADK** | GCP ingest, Gemini ADK, patches, CI/V&V, parked edge | https://github.com/team-project-pikachu/IoT-ASP/milestone/7 |

## Category labels

| Label | Meaning |
|-------|---------|
| `area:drivers` | Hardware / audio I/O / sensor drivers |
| `area:sdk` | Apple frameworks, Google Home SDK, platform SDKs |
| `area:adk` | Agent Development Kit / Gemini ADK wiring |
| `area:agentic` | Autoroute, patches, fleet agents, LLM control loops |

Also use existing `enhancement`, `mvp`, `docs`, `parked` as needed.

## Drain order (dependencies)

```text
1. Platform    contract + ingest + stub hygiene → ADK deploy (#60) → secrets/CI (#27/#63) → V&V (#64)
2. macOS       live PWA + fleet checklist (#61/#62) ← needs Platform URLs
3. iOS         shell+CI stub → drivers (motion/mic) → BT routes → telemetry bridge → on-device (#151)
                 ↘ SensorKit entitled path only after checklist (#148) — never invent approvals
4. Nest        SDK stub → event/glass model → escalation/E2E ← native hooks (#150) optional
5. Sonos       research (#39) → web (#120) → native/mac route parity (after iOS/macOS audio sessions)
```

**Invariants:** C1 phone→speaker = native A2DP (Soundcore primary). No invented OAuth / Nest tokens / SensorKit grants. Agents: `gh` / `git` / `gcloud` CLI help only for auth.

## What ships where (quick map)

| Work | Milestone | Typical labels |
|------|-----------|----------------|
| Native IoTASP / SensorKit / CoreMotion / 48 kHz mic | iOS / iPhone | `area:drivers`, `area:sdk` |
| Web blaster PWA, seeds, monitor, RLHF UI | macOS / Mac Studio | `area:agentic` |
| Nest cameras, glass shatter, Home SDK stubs | Google Home / Nest | `area:sdk`, `area:agentic` |
| Beam Gen 2 sink | Sonos | `area:drivers` |
| ADK Cloud Run, telemetry schema, Colab GCS, Pi/HomeKit parked | Platform / Agentic / ADK | `area:adk`, `area:agentic` |

## Former → current

| Former | Disposition |
|--------|-------------|
| M0 Public web blaster | Renamed → **macOS / Mac Studio** |
| M1–M4 (seeds/monitor/vib/RLHF) | Closed; issues → macOS or **iOS** (phone vib) |
| M5 SensorKit research | Closed (research done) |
| M6 LLM autoroute | Renamed → **Platform / Agentic / ADK** |
| M7 Edge companions | Closed; #14/#15 → Platform (`parked`) |
| M8 Nest MVP | Renamed → **Google Home / Nest** |
| M9 Native iOS | Renamed → **iOS / iPhone** |
| Stubs & unfinished surface | Closed; tracker → Platform |

## Related docs

- Constraints: [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) · API: [api-contract.md](api-contract.md)
- Index: [awesome-iot-asp.md](awesome-iot-asp.md) · Specs: [specs/README.md](specs/README.md)
- Legacy pointer: [mvp-roadmap.md](mvp-roadmap.md) (redirects here)
