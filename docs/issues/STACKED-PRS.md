# Balanced stacked PRs

**Election:** 2 = Balanced. Merge **bottom-up**: #57 → #66 → #70 → #71 → (PR5) → (PR6).

| # | Position | Branch | Base | Focus | URL |
|--:|----------|--------|------|-------|-----|
| 1 | 1/6 | `chore/balanced-issue-stubs` | `main` | Stub notes + CI RECORD_KEYS=24 + merge main | https://github.com/team-project-pikachu/IoT-ASP/pull/57 |
| 2 | 2/6 | `feat/balanced-shippable-slices` | `chore/balanced-issue-stubs` | #34/#22/#11/#42/#44/#45 shippable deepen | https://github.com/team-project-pikachu/IoT-ASP/pull/66 |
| 3 | 3/6 | `feat/balanced-colab-vercel-ops` | `feat/balanced-shippable-slices` | #26 dry-run→fixture + #27 names-only ops | https://github.com/team-project-pikachu/IoT-ASP/pull/70 |
| 4 | 4/6 | `feat/balanced-native-hw-research` | `feat/balanced-colab-vercel-ops` | #41/#39/#43/#14/#15/#18 research deepen | https://github.com/team-project-pikachu/IoT-ASP/pull/71 |
| 5 | 5/6 | `feat/balanced-test-native-ci` | `feat/balanced-native-hw-research` | Tests deepen #22/#26/#34 + CLT native compile-check #41 | https://github.com/team-project-pikachu/IoT-ASP/pull/72 |
| 6 | 6/6 | `feat/balanced-mvp-roadmap-docs` | `feat/balanced-test-native-ci` | MVP roadmap/closed-log #68/#69 + #61/#62 stubs | _(PR URL after open)_ |

## Owner-gated (blocked)

| Item | Gate |
|------|------|
| #27 continuous ship | Set `VERCEL_TOKEN` / `VERCEL_ORG_ID` / `VERCEL_PROJECT_ID` via 1Password `dev` → `gh secret set`. Development vault has login item `vercel - hop-ultrasonic` (credential only) — confirm discrete env keys. |
| #26 live GCS | Colab `LIVE_GCS=1` + `IOT_ASP_GCS_BUCKET` / `GCP_SA_JSON` (names only in git) |
| #39 Beam systems check | Physical Beam Gen 2 on LAN |
| #14/#15/#18 | Pi / HomeKit / chair lab — still parked |
| #41 App Store / SensorKit | Entitlement + Xcode.app device session |
| #60 ADK prod | Cloud Run / Agent Engine deploy credentials |
| #61 live backend URLs | Owner publish ingest/patch HTTPS endpoints |

Status board: [BALANCED-BUILD-STATUS.md](BALANCED-BUILD-STATUS.md).
