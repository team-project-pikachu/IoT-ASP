# Balanced stacked PRs

**Election:** 2 = Balanced. Merge **bottom-up**: #57 → #66 → #70 → #71.

| # | Position | Branch | Base | Focus | URL |
|--:|----------|--------|------|-------|-----|
| 1 | 1/4 | `chore/balanced-issue-stubs` | `main` | Stub notes + CI RECORD_KEYS=24 + merge main | https://github.com/team-project-pikachu/IoT-ASP/pull/57 |
| 2 | 2/4 | `feat/balanced-shippable-slices` | `chore/balanced-issue-stubs` | #34/#22/#11/#42/#44/#45 shippable deepen | https://github.com/team-project-pikachu/IoT-ASP/pull/66 |
| 3 | 3/4 | `feat/balanced-colab-vercel-ops` | `feat/balanced-shippable-slices` | #26 dry-run→fixture + #27 names-only ops | https://github.com/team-project-pikachu/IoT-ASP/pull/70 |
| 4 | 4/4 | `feat/balanced-native-hw-research` | `feat/balanced-colab-vercel-ops` | #41/#39/#43/#14/#15/#18 research deepen | https://github.com/team-project-pikachu/IoT-ASP/pull/71 |

## Owner-gated (blocked)

| Item | Gate |
|------|------|
| #27 continuous ship | Set `VERCEL_TOKEN` / `VERCEL_ORG_ID` / `VERCEL_PROJECT_ID` via 1Password `dev` → `gh secret set` |
| #26 live GCS | Colab `LIVE_GCS=1` + `IOT_ASP_GCS_BUCKET` / `GCP_SA_JSON` (names only in git) |
| #39 Beam systems check | Physical Beam Gen 2 on LAN |
| #14/#15/#18 | Pi / HomeKit / chair lab — still parked |
| #41 App Store / SensorKit | Entitlement + Xcode.app device session |

Status board: [BALANCED-BUILD-STATUS.md](BALANCED-BUILD-STATUS.md).
