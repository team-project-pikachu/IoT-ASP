# M8 HomeNestAlarm stub + Gemini burst detector — local evidence

- **Date (UTC):** 2026-09-08
- **Branch:** `feat/m8-homenest-gemini-stub`
- **Config:** no GoogleHomeSDK; CLT Swift 6.3.3; gcloud dry-run (no `--apply`)

## Procedure

```bash
bash scripts/ci_static_gates.sh
/Users/machine/apps/IoT-ASP/.venv/bin/python -m pytest tests -q
make home-ios-build
bash scripts/home_apis_gcloud_bootstrap.sh
```

## Observed

| Check | Result |
|-------|--------|
| `ci_static_gates` | exit 0 (`OK ci_static_gates`) |
| pytest | 280 passed, 1 skipped |
| `make home-ios-build` | `swift build` OK (HomeNestAlarm + HomeNestAlarmUI); `swift test` NOTE XCTest unavailable (CLT-only) — script exit 0 |
| gcloud bootstrap | `DRY-RUN complete` exit 0; no `gcloud services enable` executed |

No secrets, OAuth client IDs, or Nest tokens in this package. Do not scrape `console.nest.google.com`.
