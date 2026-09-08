# M9 — CI / local gates for `make home-ios-build`

**Issue:** [#112](https://github.com/team-project-pikachu/IoT-ASP/issues/112)  
**Depends on:** [#109](https://github.com/team-project-pikachu/IoT-ASP/issues/109) AppShell (PR stacked on this branch)  
**Does not replace:** M8 `scripts/home_ios_build.sh` from [#102](https://github.com/team-project-pikachu/IoT-ASP/issues/102) / PR #116 — extends presence checks only.

## Targets

| Make target | Script | Runner |
|-------------|--------|--------|
| `home-ios-presence` | `scripts/home_ios_presence_check.sh` | ubuntu CI + any host |
| `home-ios-build` | `scripts/home_ios_build.sh` | macOS / Swift CLT |

Missing files → **exit 1** with `FAIL:` (no silent skip). Proprietary GoogleHomeSDK remains optional via `#if canImport`.

## Related

- Milestone shell: [M9-native-ios-app-shell.md](M9-native-ios-app-shell.md)
- Workflow docs: [../ci.md](../ci.md)
- Sibling #110 / #111 may add their own `sensorkit-stub-build` / motion targets — keep those separate from `home-ios-build`.
