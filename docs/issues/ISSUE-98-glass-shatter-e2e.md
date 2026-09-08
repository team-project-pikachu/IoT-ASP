# ISSUE-98 — Glass shatter E2E acceptance

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/98  
**Classification:** offline pytest + owner lab checklist  
**Status:** offline path documented and tested — physical Nest / notify pending

## Goal (from issue)

Simulate glass shatter → classify → escalate louder → snapshot context stub → notify pending flag.

## Offline checklist (CI / laptop)

1. [x] `offline_classify` with Nest acoustic + strong phone US-band corroboration → `glass_shatter`
2. [x] Weaker corroboration stays `sound_burst` (no false glass escalation)
3. [x] `escalation_hint` for glass sets `alarmState=triggered` and `volBlast=true`
4. [x] Hold / Manual yields empty hint
5. [x] Wire dict has no clip URL / token / raw device-id sentinels
6. [x] Notify / Automation called out as **pending** (not claimed shipped)
7. [x] `pytest tests/test_glass_shatter_e2e.py -q` exits 0

```bash
python3 -m pytest tests/test_glass_shatter_e2e.py -q
```

## Owner lab checklist (optional — not required to merge docs/tests)

Print / tick on device when Nest + HomeNest / PWA UI are linked:

1. [ ] Nest CameraSound (or simulate) observed without scraping consoles from an agent
2. [ ] Classification surfaces as `glass_shatter` or documented `sound_burst` fallback
3. [ ] Louder escalation audible / `volBlast` true; Hold clears
4. [ ] Snapshot context stub present without leaking `previewUrl` to public telemetry
5. [ ] Notify / Automation still marked pending until #97 ships
6. [ ] No secrets in screen recordings uploaded to the public repo

## Didn't

- Claim physical shatter trial completed
- Claim push notify shipped
- Require live Gemini or OAuth for CI green

## Next

- Owner paste lab outcomes into the GitHub issue comment
- Wire HomeNest simulate button / PWA UI via #97 / #101 when those PRs land
