# Testing plan — SEBoK Verification & Validation

**TL;DR:** Verify in CI (`make test`, autoroute dry-run, HTML gates). Validate in the field ([UAT.md](UAT.md)). Matrix rows stay `stub` until fresh `.vv/` evidence. No parallel test framework — extend SEBoK.

**Product:** IoT-ASP / hop-ultrasonic · **Index:** [README.md](README.md)  
**Companion:** [UAT.md](UAT.md) · [PRD.md](PRD.md) · [roadmap.md](roadmap.md) · [architecture-pwa.md](architecture-pwa.md) · [test-traceability.md](test-traceability.md) · [vv/README.md](vv/README.md) · [`.vv/matrix.md`](../.vv/matrix.md)

## SEBoK framing

| Term | Meaning here |
|------|----------------|
| **Verification** | Built right — schema, clamps, CI, stub builds |
| **Validation** | Right system — field behavior (see UAT) |
| **Methods** | Inspection, analysis, demonstration, test |
| **Evidence** | `.vv/<issue>/`; `stub`→`pass` only with fresh results |
| **Promotion** | Project #5 Done needs that evidence |

## Test levels

| Level | Scope | Primary tools |
|-------|-------|---------------|
| **Unit** | Clamps, parsers, alarm state, HTML invariants | `pytest`, `tests/test_public_html.py` |
| **Integration** | Autoroute dry-run, patch validate, ADK package import | `scripts/autoroute_dev.sh`, `make` targets |
| **System** | CI workflow, deploy gates, home-ios-build stub | `.github/workflows/ci.yml`, `make home-ios-build` |
| **Acceptance (UAT)** | Fleet phones, A2DP, Nest live, Sonos | [UAT.md](UAT.md), issues #62, #151, #89 |

## Methods → examples

| Method | Examples |
|--------|----------|
| Inspection | No `navigator.bluetooth` TX; no secrets in `public/`; SensorKit gate comments |
| Analysis | Nyquist vs 23 kHz; BT codec roll-off notes; capability matrix |
| Demonstration | Stub Nest glass UI; native impulse simulate |
| Test | pytest; Playwright e2e smoke; autoroute refuse bad patch |

## Map existing repo evidence

| Gate | Command / artifact | Level |
|------|--------------------|-------|
| Static HTML / Hold / secrets | CI job `HTML Hold + secrets + patch.json` | System |
| Public HTML unit | `tests/test_public_html.py` | Unit |
| Autoroute clamps | `bash scripts/autoroute_dev.sh` | Integration |
| Full local | `make test` / `make all` | System |
| E2E smoke | Playwright `tests/e2e` | System |
| Native stub | `make home-ios-build` (or documented equiv) | System |
| Field checklist | Issue #62 | Acceptance |
| On-device iOS | Issue #151 | Acceptance |
| SEBoK matrix pass | Issue #64 + `.vv/` | V&V |

## Negative controls / regression gates

| Control | Intent |
|---------|--------|
| Bad patch rejected | `validate_patch` / clamps refuse illegal vol/band |
| Hold blocks autoroute apply | HOLD1 |
| No Web Bluetooth TX | C1 |
| Button / Logseq TDZ regressions | Keep hop UI wired after refactors (#139 class bugs) |
| No silent reintroduction of removed **10–20 Hz** LF UI without HW gate + PRD election | Align with current ship slice (default **17–23 kHz**); if LF returns, must be gated + documented |
| No invented Nest/SensorKit secrets in fixtures | grep / CI |

## “Done” per milestone

| Milestone | Done means |
|-----------|------------|
| **Platform** | CI green; contract intact; #64 evidence advancing; ADK path documented (#60) |
| **macOS** | Prod PWA usable; #61/#62 field evidence; Hold works |
| **iOS** | Stub CI green; on-device #151 pack; sensors→telemetry; SensorKit remains stub until #148 |
| **Nest** | Stub-builds green; glass model demo; live Nest only after #93 evidence |
| **Sonos** | Research AC closed or integrated without breaking Soundcore-primary C1 |

## Drain order for evidence

1. Automate verify (CI) → 2. macOS field (#62) → 3. iOS on-device (#151) → 4. Nest live (owner) → 5. Sonos physical route.

## Related issues

- #64 SEBoK matrix pass · #62 field · #151 iOS UAT · Platform UAT evidence pack (if filed)
