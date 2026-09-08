# ISSUE-62 — MVP field acceptance + promote Playwright e2e

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/62  
**Classification:** checklist + e2e deepen (Balanced PR7); **field lab owner-gated**  
**Status:** checklist + local/CI informative e2e assertions deepened — not claimed as required check

## Field checklist (3-phone fleet)

Print / tick during lab (Safari + native A2DP only — C1):

1. [ ] Open live PWA on phone 1/2/3 (or local `make e2e` host for desktop smoke)
2. [ ] Each phone paired 1:1 Soundcore via **Settings → Bluetooth** (not Web Bluetooth)
3. [ ] Mode Blaster/TX · Signal on · hops incoherent (independent seeds)
4. [ ] Hold / Manual freezes patch apply
5. [ ] Simulate impulse (web) → volBlast / alarm armed→triggered→sustaining
6. [ ] Copy fleet_log JSONL → keys match Python `RECORD_KEYS` (#22)
7. [ ] Optional live backend: `?patch=` + `?telemetry=` (#61) — skip if URLs unset
8. [ ] No API keys visible in page source / Network (names only)

## Local e2e

```bash
make e2e   # serves public/ + Playwright smoke (tests/e2e/)
```

PR7 adds desktop assertions for fleet panel + Simulate impulse + gyro keys. Honesty: e2e remains **informative** (`ci.yml` job `e2e smoke`) until owner elects required-check promotion with `#63`.

## Didn't

- Claim field lab completed
- Force e2e as a required check without owner `#63` decision
- Drive a browser from agent sessions for this stack (CLI/pytest only)

## Next

- Owner run checklist on three phones; paste outcomes into issue comment
- Optionally promote `e2e` job in CI after browsers cache is budgeted
