# V&V — M8 Nest / Gemini / Home iOS (PR #105)

**Config item:** `native/IoTASPHome/`, `services/gemini-burst-detect/`, `scripts/home_ios_build.sh`, `scripts/home_apis_gcloud_bootstrap.sh`  
**Date (UTC):** 2026-09-08T06:22:17Z  
**Revision:** `e5b82a7de44b65d9cfdef844879b1af5c8b87f63` (`feat/m8-nest-gemini-home-ios`)  
**Host:** Darwin 25.6.0 arm64  
**Swift:** swift-driver version: 1.148.6 Apple Swift version 6.3.3 (swiftlang-6.3.3.1.3 clang-2100.1.1.101)  
**Secrets:** none recorded (emails / tokens scrubbed)

## Procedure

```bash
git rev-parse HEAD
make home-ios-build
python3 -m pytest tests/test_gemini_burst_detect.py -q
bash scripts/home_apis_gcloud_bootstrap.sh   # default = dry-check (no --apply)
test -f native/IoTASPHome/Package.swift
test -f services/gemini-burst-detect/detect.py
test -f scripts/home_ios_build.sh
test -f scripts/home_apis_gcloud_bootstrap.sh
test -f reference/nest-device-access/KNOWLEDGE-INGEST.md
```

Artifacts under `.vv/m8/`: `META.txt`, `home-ios-build.{stdout,stderr}.txt`, `pytest-gemini-burst.{stdout,stderr}.txt`, `home-gcloud-dry.{stdout,stderr}.txt`, `presence.txt`.

## Observed results

| Check | Exit | Result |
|-------|-----:|--------|
| `make home-ios-build` (`swift build`) | 0 | Stub package builds; GoogleHomeSDK not required |
| `swift test` inside home-ios-build | soft-0 | NOTE: XCTest unavailable on CLT-only host (expected soft gate) |
| `pytest tests/test_gemini_burst_detect.py -q` | 0 | 7 passed in 0.01s |
| `home_apis_gcloud_bootstrap.sh` (default dry) | 0 | Dry-check prints service names; no `--apply` mutations |
| Presence of M8 paths | 0 | Package.swift: present; detect.py: present; home_ios_build.sh: present; home_apis_gcloud_bootstrap.sh: present; KNOWLEDGE-INGEST.md: present |

gcloud dry excerpt (redacted):

```text
=== gcloud identity (dry check; emails redacted in logs) ===
account_configured=yes
project=bear-iot-asp-rec
expected_owner_configured=yes
owner_account_match=yes

=== ADC / auth status (no account emails printed) ===
active_credential_status=*

=== Required / related API service names (document only) ===
 - aiplatform.googleapis.com
 - pubsub.googleapis.com
 - smartdevicemanagement.googleapis.com
Home APIs iOS OAuth / Device & Automation: Google Home Developer Console (not a gcloud services enable alone).
CLI surfaces to explore later: gcloud ai … ; gcloud beta ai … ; gcloud alpha ai …

=== Enablement commands (printed; applied only with --apply) ===
gcloud services enable aiplatform.googleapis.com --project=${PROJECT}
```

## Pass/fail

| Requirement | Status |
|-------------|--------|
| M8 Home iOS stub `swift build` | **PASS** |
| Detector pytest (thresholds / classes / wire keys) | **PASS** |
| gcloud bootstrap dry-check (no paid enable) | **PASS** |
| XCTest under full Xcode.app | **BLOCKED — CLT-only host** |
| Live GoogleHomeSDK / Nest OAuth / metered Gemini | **PENDING — owner-gated** |
| #101 PWA glass_shatter UI | **PENDING — not in this PR** |
| #102 Swift Playgrounds workflow | **PENDING — not in this PR** |

## Notes

- Evidence refresh for Copilot thread on `docs/milestones/M8-nest-gemini-soundburst-mvp.md` (`.vv/` required by `CLAUDE.md` / `.claude/rules/docs-and-specs.md`).
- No API keys, OAuth tokens, or personal street addresses included.
