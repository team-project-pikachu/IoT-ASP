# Balanced stacked PRs

**Election:** 2 = Balanced. Merge **bottom-up**: #57 → #66 → #70 → #71 → #72 → #73 → #75 → #76 → **M8 Home/Nest**.

| # | Position | Branch | Base | Focus | URL |
|--:|----------|--------|------|-------|-----|
| 1 | 1/9 | `chore/balanced-issue-stubs` | `main` | Stub notes + CI RECORD_KEYS=24 + merge main | https://github.com/team-project-pikachu/IoT-ASP/pull/57 |
| 2 | 2/9 | `feat/balanced-shippable-slices` | `chore/balanced-issue-stubs` | #34/#22/#11/#42/#44/#45 shippable deepen | https://github.com/team-project-pikachu/IoT-ASP/pull/66 |
| 3 | 3/9 | `feat/balanced-colab-vercel-ops` | `feat/balanced-shippable-slices` | #26 dry-run→fixture + #27 names-only ops | https://github.com/team-project-pikachu/IoT-ASP/pull/70 |
| 4 | 4/9 | `feat/balanced-native-hw-research` | `feat/balanced-colab-vercel-ops` | #41/#39/#43/#14/#15/#18 research deepen | https://github.com/team-project-pikachu/IoT-ASP/pull/71 |
| 5 | 5/9 | `feat/balanced-test-native-ci` | `feat/balanced-native-hw-research` | Tests deepen #22/#26/#34 + CLT native compile-check #41 | https://github.com/team-project-pikachu/IoT-ASP/pull/72 |
| 6 | 6/9 | `feat/balanced-mvp-roadmap-docs` | `feat/balanced-test-native-ci` | MVP roadmap/closed-log #68/#69 + #61/#62 stubs | https://github.com/team-project-pikachu/IoT-ASP/pull/73 |
| 7 | 7/9 | `feat/balanced-api-contract-vv` | `feat/balanced-mvp-roadmap-docs` | api-contract + fleet polish + #64 software verify | https://github.com/team-project-pikachu/IoT-ASP/pull/75 |
| 8 | 8/9 | `feat/balanced-ops-secrets-adk` | `feat/balanced-api-contract-vv` | #27 inventory + #63 status + #60 dry-check | https://github.com/team-project-pikachu/IoT-ASP/pull/76 |
| 9 | 9/9 | `feat/m8-nest-gemini-home-ios` | `feat/balanced-ops-secrets-adk` | M8 Nest+Gemini+glass shatter + IoTASPHome stub build | https://github.com/team-project-pikachu/IoT-ASP/pull/105 |

## Owner-gated (blocked)

| Item | Gate |
|------|------|
| #27 continuous ship | `VERCEL_ORG_ID` + `VERCEL_PROJECT_ID` present in Actions; **`VERCEL_TOKEN` still MISSING**. 1Password Development item title `vercel - hop-ultrasonic` (values never in git). |
| #26 live GCS | Colab `LIVE_GCS=1` + `IOT_ASP_GCS_BUCKET` / `GCP_SA_JSON` (names only in git) |
| #39 Beam systems check | Physical Beam Gen 2 on LAN |
| #14/#15/#18 | Pi / HomeKit / chair lab — still parked (#15 ≠ Google Home M8) |
| #41 App Store / SensorKit | Entitlement + Xcode.app device session |
| #60 ADK prod | Cloud Run / Agent Engine deploy credentials |
| #61 live backend URLs | Owner publish ingest/patch HTTPS endpoints |
| #63 ruleset apply | Live `main-protection` already **active** (id `22505825`) — residual: keep JSON ↔ CI names in sync |
| #64 V&V pass rows | Software rows `in_progress`; `pass` needs field `#62` evidence |
| M8 #83–#104 | Nest/OAuth/Gemini live: **betty@bearresearch.io** + 1Password `dev`; no browser agent login |

Status board: [BALANCED-BUILD-STATUS.md](BALANCED-BUILD-STATUS.md).

## GitHub Project board

- **IoT-ASP** project #5 (`PVT_kwDODokw1c4BixEd`) — owner `team-project-pikachu`
- M8 issues #83–#104 added; Status → In Progress for active stub work
- Milestone: https://github.com/team-project-pikachu/IoT-ASP/milestone/9


## Outstanding snapshot (log-only — 2026-09-08)

Logged via `gh` to open PRs/issues + project **5** (no new feature code).

| Theme | Outstanding |
|-------|-------------|
| Merge stack | `#66`→`#70`(CONFLICTING)→`#71`; ops tip `#75`→`#76`(CONFLICTING)→`#105` |
| Secrets | `#27` Vercel Actions secrets; webhook deploy config `#59` |
| GCS | `#26` live Colab GCS (`LIVE_GCS` / bucket / SA) |
| Nest console | `#83` `#85` `#93` OAuth/Premium — betty@bearresearch.io |
| HW | `#104` ladder, `#39` Beam, `#14` Pi, `#18` chair — parked |
| Field | `#61` live URLs → `#62` 3-phone acceptance → `#64` V&V pass |
| De-dupe merges | GEN_MARK `#35` vs `#66`/`#72`; impulse `#54` vs `#66`; closed-log `#73`/`#74`/`#79` |

Project Status: In Progress = stub tip + active stack PRs; Todo = owner-gated waiting; Backlog = parked HW/OAuth.
