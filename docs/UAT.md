# UAT — User Acceptance Test plan (SEBoK-aligned)

**Product:** IoT-ASP / hop-ultrasonic  
**Traceability:** [PRD.md](PRD.md) ↔ [TESTING_PLAN.md](TESTING_PLAN.md) ↔ [roadmap.md](roadmap.md) ↔ `.vv/matrix.md`  
**Guide:** [vv/README.md](vv/README.md) (NASA SEBoK-style V&V)

## Purpose

**Validation** (“right system”): humans accept that each OS/product surface meets PRD intent in real environments.  
**Verification** (“built right”) lives primarily in [TESTING_PLAN.md](TESTING_PLAN.md) / CI / `.vv/` packs.

## Roles

| Role | Does |
|------|------|
| **Owner / user** | Device pairing, Nest OAuth, SensorKit entitlement, field fleet runs, UAT sign-off |
| **Agent** | Automate verify gates, draft evidence stubs, update matrix Status only with attached results — never invent secrets |

## Environments

| Env | Use |
|-----|-----|
| Vercel **prod** hop URL | macOS / web PWA acceptance |
| iPhone (fleet 16/14) + Soundcore A2DP | iOS + C1 TX |
| Mac Studio + Sonos Beam Gen 2 | macOS / Sonos route |
| Simulator / CI | Stub-only — **not** UAT for ultrasonic or A2DP |

## Entry / exit criteria

**Entry (per surface):** PRD FRs mapped; CI verify green for that surface’s automatable gates; no invented OAuth/entitlement claims.  
**Exit:** UAT checklist signed with evidence paths under `.vv/` or linked issue comments; Project #5 Status → Done only with fresh evidence ([vv/README.md](vv/README.md)).

## Acceptance by milestone

### iOS / iPhone — https://github.com/team-project-pikachu/IoT-ASP/milestone/10

| AC | Type | Owner-gated? | Evidence |
|----|------|--------------|----------|
| Native shell builds (`make home-ios-build` or equiv) | Verify+UAT demo | No (CI) | #112 |
| Mic 48 kHz pref; AEC/NS/AGC off (or honest OS override) | UAT on device | Yes | #141, #151 |
| CoreMotion samples → impulse/vib | UAT | Yes | #140, #111 |
| A2DP Soundcore TX + systems-check route | UAT | Yes | #146, C1 |
| Telemetry/patch bridge schemaVersion 1 | Verify + UAT | Partial | #147 |
| SensorKit entitled readers | UAT | **Yes** (#148) | stub until approved |
| Nest/Glass tab hooks (native-only demo OK) | Demo | No tokens | #150 |

### macOS / Mac Studio — https://github.com/team-project-pikachu/IoT-ASP/milestone/1

| AC | Type | Owner-gated? | Evidence |
|----|------|--------------|----------|
| Prod PWA Signal on / hop TX | UAT | Yes (devices) | README live URL |
| Fleet 3-phone checklist | UAT | Yes | #62 |
| Live telemetry + patch URLs | UAT | Yes (secrets) | #61, #27 |
| Monitor / seeds / Hold behavior | UAT | Partial | #3, #2, HOLD1 |

### Google Home / Nest — https://github.com/team-project-pikachu/IoT-ASP/milestone/9

| AC | Type | Owner-gated? | Evidence |
|----|------|--------------|----------|
| SDK/app stub-builds without proprietary secrets | Verify | No | #91, #112 |
| Glass shatter model + wiring (stub) | Demo | No | #96–#98 |
| Live Nest camera / OAuth | UAT | **Yes** (#93) | never invent client IDs |
| Burst → escalate E2E | UAT | Yes when unparked | #89 |

### Sonos — https://github.com/team-project-pikachu/IoT-ASP/milestone/12

| AC | Type | Owner-gated? | Evidence |
|----|------|--------------|----------|
| Beam Gen 2 reachable as system/AirPlay sink | UAT | Yes | #39 |
| Web blaster can target Sonos without breaking C1 Soundcore primary | UAT | Yes | #120 |
| DSP/resample honesty documented | Inspection | No | docs |

### Platform / Agentic / ADK — https://github.com/team-project-pikachu/IoT-ASP/milestone/7

| AC | Type | Owner-gated? | Evidence |
|----|------|--------------|----------|
| Autoroute dry-run + clamps | Verify | No | `scripts/autoroute_dev.sh` |
| ADK deploy path documented | Verify/Demo | Partial | #60 |
| SEBoK matrix rows for C1–C6/SCH1/HOLD1 | V&V | Yes for field rows | #64, `.vv/matrix.md` |
| No secrets in repo | Verify | No | CI HTML/secrets gates |

## Traceability (PRD → test → evidence)

| PRD | Verify | Validate / UAT | Evidence root |
|-----|--------|----------------|---------------|
| FR-US / FR-TX / C1 | code audit, CI | device A2DP | `.vv/` + #151/#62 |
| FR-TEL / SCH1 | pytest / contract | live beacon | api-contract + #61 |
| FR-HOLD / HOLD1 | unit/UI | Hold blocks patch | `.vv/matrix.md` |
| FR-NEST | stub build | owner OAuth E2E | Nest milestone |
| Entitlements | docs inspection | checklist #148/#93 | never fake |

## Explicit owner-gated vs automatable

| Automatable (agents OK) | Owner-gated |
|-------------------------|-------------|
| pytest, Playwright smoke, autoroute dry-run, mdc check, home-ios-build stub | Nest OAuth, SensorKit approval, 3-phone field pairing, Sonos physical route, entitlement flips |

## Sign-off template (per surface)

```text
Surface: <iOS|macOS|Nest|Sonos|Platform>
Date / operator:
Env (device / iOS / URL):
ACs passed:
Evidence paths / issue comments:
Fail / defer:
```
