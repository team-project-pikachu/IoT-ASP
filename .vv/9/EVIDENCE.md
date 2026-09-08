# SEBoK V&V evidence — Issue #9 (SensorKit research)

| Field | Value |
|-------|--------|
| **Issue** | [#9](https://github.com/team-project-pikachu/IoT-ASP/issues/9) SensorKit / native iOS shell + edge companions (research) |
| **CI class** | Research deliverable (docs + evidence); **no** native entitlement |
| **UTC** | `2026-09-08T00:15:04Z` |
| **Revision** | `e41c3c0e76ef9e0d9ddb59995cc7faf769a8bb79` |
| **Plan todo** | `exec-9-13-research` |
| **Project board** | Integrate lane owns Status → Done / issue comment |

---

## Requirements capture

| Req ID | Statement | Source |
|--------|-----------|--------|
| R9-1 | Web cannot use SensorKit; requires native iOS + entitlement | Issue #9 body; Apple SensorKit docs |
| R9-2 | Document edge companions #14 Pi5, #15 Apple Home, #18 node-3 | Issue #9 body; plan lane 5 |
| R9-3 | Chrome iOS sensor arm checklist | Plan lane 5; DESIGN_CONSTRAINTS C1 |
| R9-4 | No native Xcode entitlement work this wave | Plan non-goals / lane 5 |

Canonical closeout: [`docs/sensorkit-research-closeout.md`](../../docs/sensorkit-research-closeout.md).

---

## Verification (built the research right)

| Procedure | Expected | Observed | Pass |
|-----------|----------|----------|------|
| V9-1 Closeout doc exists and states Web ≠ SensorKit | Explicit entitlement + no Web API | `docs/sensorkit-research-closeout.md` §R1 | **PASS** |
| V9-2 Companions table links #14/#15/#18 | Three issues with roles | Closeout §R2 | **PASS** |
| V9-3 Chrome iOS arm doc linked | Checklist file present | `docs/sensors-chrome-ios.md` + closeout §R3 | **PASS** |
| V9-4 Native entitlement deferred | Explicit non-goal | Closeout §R4; `docs/native-xcode.md` parked | **PASS** |
| V9-5 Systems check honesty | SensorKit row **na** in app | `public/index.html` Systems check SensorKit row | **PASS** |
| V9-6 Knowledge ingest present | Apple SensorKit notes on disk | `reference/knowledge/apple-sensorkit/` | **PASS** |

---

## Validation (right research product)

| Procedure | Expected | Observed | Pass |
|-----------|----------|----------|------|
| Val9-1 Companions ≠ SensorKit substitutes | Text states parallel paths | Closeout §R2 | **PASS** |
| Val9-2 Carrier TX still A2DP-only | C1 unchanged | DESIGN_CONSTRAINTS C1; closeout policy coupling | **PASS** |
| Val9-3 No entitlement provisioning artifacts | No Xcode / `.mobileprovision` added under #9 | Research docs only this lane | **PASS** |

---

## Negative controls

| Control | Expected | Observed | Pass |
|---------|----------|----------|------|
| N9-1 Claim “Safari has SensorKit” | Must not appear as supported | Systems check **na**; closeout forbids | **PASS** |
| N9-2 Treat #14/#15/#18 as entitlement unlock | Must not | Documented as companions only | **PASS** |

---

## Research completeness checklist

- [x] Web cannot SensorKit documented
- [x] Companions #14 / #15 / #18 linked with roles
- [x] Chrome iOS sensor arm checklist present
- [x] No native entitlement this wave stated
- [x] Evidence under `.vv/9/`

---

## Promotion note

Research ACs for #9 are **complete**. Board Status → Done and the “implementation parked” issue comment are owned by **`integrate-deploy-board`**. If the Project gate requires Gemini #12 evidence-green first, keep #9 research Done-ready but defer board flip until that gate clears.

**Result:** **PASS** (research scope).

## Verify stamp

| Field | Value |
|-------|--------|
| **Ran UTC** | `2026-09-08T00:17:45Z` |
| **Command** | `bash .vv/9/verify.sh` |
| **Result** | OK |
