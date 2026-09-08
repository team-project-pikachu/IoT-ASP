# V&V — #62 software / Playwright MVP acceptance

**Config:** `tests/e2e/public_smoke.spec.mjs` (`MVP field acceptance (#62)` + public blaster smoke)  
**Docs:** `docs/field-acceptance-m0.md`, `docs/issues/ISSUE-62-mvp-field-acceptance-e2e.md`, `docs/specs/62-mvp-field-acceptance-e2e.md`  
**Date:** 2026-09-08 (software slice)  
**Revision:** branch `feat/62-field-acceptance-e2e`  
**Host:** local / GitHub Actions `e2e smoke` (Chromium; **not** Safari/A2DP)

## Procedure

```bash
make e2e
# or: bash tests/e2e/run.sh
# MVP-only: bash tests/e2e/run.sh --grep "MVP field acceptance"
```

Env:

| Var | Default | Notes |
|-----|---------|-------|
| `PLAYWRIGHT_BROWSERS_PATH` | `/opt/pw-browsers` | CI sets `$RUNNER_TEMP/pw-browsers` and runs `npx playwright install --with-deps chromium` |
| `E2E_PORT` | `8765` | Local static server for `public/` |

## Observed results (fill on each green run)

| Gate | Exit | Result | Notes |
|------|------|--------|-------|
| `pytest tests/test_issue_62_field_e2e.py` | 0 | **5 passed** (2026-09-08, wt-62) | Offline docs/hooks |
| `make e2e` / `tests/e2e/run.sh` | 0 | Local may lack `chromium_headless_shell-1194`; **CI installs browsers** | Record SHA on green Actions |
| Soundcore warning + Systems check | _TBD_ | _TBD_ | |
| suddenFreq force rotate | _TBD_ | _TBD_ | Uses `__hop.forceSuddenRotate` |
| nightNY day/night inject | _TBD_ | _TBD_ | Uses `__hop.setTestNowMs` |
| fleet_log ↔ `RECORD_KEYS` | _TBD_ | _TBD_ | |
| Hold / Manual | _TBD_ | _TBD_ | |

## CI policy

`e2e smoke` remains **informative** (not a required ruleset context). See ISSUE-62 CI decision table and `#63`.

## Pass / fail summary

| Gate | Status |
|------|--------|
| Software Playwright MVP suite | **implemented** — run evidence above |
| 3-phone field lab | **not claimed** — see `FIELD-PASS.md` |


## Latest local run

- **When:** 2026-09-08T07:30Z (approx)
- **Command:** `PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright bash tests/e2e/run.sh`
- **Result:** `16 passed (16.4s)`, `OK e2e`, exit 0
- **Browsers:** `chromium_headless_shell-1194` (manual zip when CDN flaked); CI uses `npx playwright install --with-deps chromium`
- **Note:** `playwright.config.mjs` falls back to full Chromium 1194 if headless_shell-1194 is absent
