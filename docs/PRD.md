# IoT-ASP / hop-ultrasonic — Product Requirements Document (PRD)

**TL;DR:** Phones hop near-ultrasound (17–23 kHz) over **native A2DP** to Soundcore. Browser polls patches; Gemini/ADK stays on the backend. Ship by surface (iOS → macOS → Nest → Sonos) with Platform first. Never invent OAuth/SensorKit secrets.

**Status:** living · **Aligned to:** [roadmap.md](roadmap.md) · [UAT.md](UAT.md) · [TESTING_PLAN.md](TESTING_PLAN.md)  
**Board:** [Project 5](https://github.com/orgs/team-project-pikachu/projects/5) · **Index:** [README.md](README.md)  
**Issue titles:** `{Surface}: …` (`iOS:` · `macOS:` · `Nest:` · `Sonos:` · `Platform:` / `ADK:` / `Agentic:`)

## 1. Vision / problem

**What:** Multi-phone hop fleet for ASP experiments — TX via system Bluetooth A2DP (Soundcore primary), optional Mac Studio + Sonos Beam, decoupled control plane (telemetry → GCP/ADK → clamped `patch.json`), optional Nest glass/burst story.

**Why it’s hard:** No Web Bluetooth for carrier audio; SensorKit and Nest OAuth are owner-gated. Stay honest about HW; never invent secrets.

## 2. Goals & non-goals

### Goals
- Ship usable **17–23 kHz** hop TX/RX paths on phone (web PWA + native iOS) with 48 kHz preference and AEC/NS/AGC off where supported.
- Keep **C1**: phone → speaker = **native A2DP only** (not Web Bluetooth).
- Maintain `schemaVersion: 1` telemetry/patch contract ([api-contract.md](api-contract.md)).
- Organize delivery by **OS/product milestones** + `area:*` labels ([roadmap.md](roadmap.md)).
- SEBoK-style V&V evidence before calling a surface “done” ([TESTING_PLAN.md](TESTING_PLAN.md), `.vv/matrix.md`).

### Non-goals
- Inventing OAuth client IDs, Nest tokens, or SensorKit entitlement approvals.
- Agents automating Apple/Google browser OAuth (CLI help only: `gh` / `git` / `gcloud`).
- Claiming ambient-light or other sensors the public iOS APIs do not provide.
- Reopening closed M5 SensorKit **research** as literature work (build + integrate only).

## 3. Users & surfaces

| Surface | Who / where | Primary artifact |
|---------|-------------|------------------|
| **iPhone / iOS** | Fleet operators on device | `native/IoTASP/`, Safari/Chrome PWA |
| **Mac Studio / macOS** | Desktop ops, Sonos route from Mac | `public/` hop blaster, Studio tooling |
| **Web PWA hop-ultrasonic** | Same blaster on Vercel | Live URL in README; mirror `public/` |
| **Google Home / Nest** | Home alarm / camera / glass shatter | Home SDK stubs, SDM event story |
| **Sonos Beam Gen 2** | Secondary audio sink | System/AirPlay route; DSP honesty |

## 4. Product pillars → milestones

| Pillar | Milestone | URL |
|--------|-----------|-----|
| Native sensors + on-device ultrasonic | **iOS / iPhone** | https://github.com/team-project-pikachu/IoT-ASP/milestone/10 |
| Desktop web blaster + fleet ops | **macOS / Mac Studio** | https://github.com/team-project-pikachu/IoT-ASP/milestone/1 |
| Nest cam / burst / glass shatter | **Google Home / Nest** | https://github.com/team-project-pikachu/IoT-ASP/milestone/9 |
| Beam Gen 2 sink policy | **Sonos** | https://github.com/team-project-pikachu/IoT-ASP/milestone/12 |
| Ingest, ADK, CI, V&V, parked edge | **Platform / Agentic / ADK** | https://github.com/team-project-pikachu/IoT-ASP/milestone/7 |

## 5. Feature categories (requirements)

| Label | Requirements (summary) |
|-------|------------------------|
| `area:drivers` | CoreMotion suite; 48 kHz mic; A2DP/route I/O; honest HW capability matrix; Sonos/Soundcore sinks |
| `area:sdk` | SensorKit stubs; Home SDK / Playground stubs; Info.plist + entitlement scaffolding (no fake grants) |
| `area:adk` | Google ADK agent package; Cloud Run / Agent Engine deploy path; `adk_agent/` hygiene |
| `area:agentic` | suddenFreq → patch loop; fleet telemetry; Hold/Manual; stub/shim audit; autoroute clamps |

## 6. Functional requirements

| ID | Requirement |
|----|-------------|
| FR-US | Default TX band **17–23 kHz**; prefer 48 kHz capture; expose Nyquist honesty in systems check |
| FR-TX | Carrier audio out via **system A2DP** (Soundcore) or documented Sonos/Mac route — never Web Bluetooth TX |
| FR-MIC | Mic path supports micDiff / bandEnergyUs style metering; AEC/NS/AGC off when OS allows |
| FR-MOT | Motion/vib samples feed impulse / vibClass / telemetry `ax..gz` |
| FR-TEL | Telemetry POST + patch poll per [api-contract.md](api-contract.md); no Vertex keys in frontend |
| FR-FLEET | 3-phone incoherent hops; continuous AC power assumption (`power=ac120`) |
| FR-NEST | Burst / glass_shatter event model + stub Home paths; live Nest only after owner OAuth evidence |
| FR-HOLD | Hold / Manual freezes remote patch apply |

## 7. Non-functional

- Privacy: no site PII in telemetry; usage strings accurate; recording consent for Nest paths.
- Entitlements: SensorKit / Nest OAuth **owner-gated**; agents do not invent approvals.
- Scientific honesty: document BT resampling / DSP roll-off (Soundcore, Sonos); no fake lux streams.
- Security: secrets via env / 1Password refs only; CI must not commit tokens.

## 8. Success metrics / acceptance

- CI: `make test` / pytest / Playwright e2e smoke green on main ship path.
- Field: #62 3-phone checklist; iOS on-device #151; Nest E2E when unparked.
- V&V: #64 matrix rows move `stub` → `pass` only with `.vv/` evidence ([UAT.md](UAT.md)).
- Regression: button wiring / no accidental reintroduction of removed LF UI without gated HW + AC (see TESTING_PLAN negative controls).

## 9. Roadmap drain order

See [roadmap.md](roadmap.md). Short form: **Platform → macOS → iOS → Nest → Sonos**.

## 10. Open questions / owner-gated

- SensorKit entitlement approval status (checklist #148) — **unknown until owner records evidence**.
- Nest OAuth client / consent for bettyctai@gmail.com — **owner steps only** (#93).
- Sonos Beam as primary vs secondary sink vs Soundcore — product election (#39/#120).
- Whether ambient / LF paths remain research-only after LF UI removal on web ship slice.

## Related

- Constraints: [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) · Index: [README.md](README.md) · SEBoK guide: [vv/README.md](vv/README.md)
