## Summary

<!-- What changed and why (breaking-change risk?). -->

## Related issue (required)

PRs that touch product/docs/CI must link a tracked issue (Project 5 Todo: #12 / #16 / #17 / #9 / #13, or another open issue).

Use one of:

- `Fixes #N`
- `Closes #N`
- `Resolves #N`
- `Related: #N`

Issue: 

## Checklist

- [ ] No breaking wire changes without `schemaVersion` bump (`docs/api-contract.md`)
- [ ] `vol_hard_max` stays `100` (UI percent) — see `services/autoroute-adk/iot_asp_autoroute/clamps.py`
- [ ] Hold / Manual still freezes remote patch apply
- [ ] No API keys / Gemini credentials in `public/` HTML
- [ ] Local gate: `bash scripts/autoroute_dev.sh` and `bash scripts/ci_static_gates.sh`

## Test plan

- [ ] CI green on this PR (`autoroute dry-run + clamps`, `HTML Hold + secrets + patch.json`, `PR must reference an issue`, `tests`, `mdc check`)
