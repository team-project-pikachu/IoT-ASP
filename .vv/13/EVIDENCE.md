# SEBoK V&V evidence — Issue #13 (multi-LLM registry sketch)

| Field | Value |
|-------|--------|
| **Issue** | [#13](https://github.com/team-project-pikachu/IoT-ASP/issues/13) Autoroute multi-LLM registry (post-Gemini) |
| **CI class** | Design sketch only; **no** production non-Gemini LLM calls |
| **UTC** | `2026-09-08T00:15:04Z` |
| **Revision** | `e41c3c0e76ef9e0d9ddb59995cc7faf769a8bb79` |
| **Plan todo** | `exec-9-13-research` |
| **Project board** | Integrate lane owns Status → Done / issue comment |

---

## Requirements capture

| Req ID | Statement | Source |
|--------|-----------|--------|
| R13-1 | Registry of provider adapters + model allowlist | Issue #13 body |
| R13-2 | Same patch schema + safety clamps | Issue #13; api-contract; clamps.py |
| R13-3 | Seat/cost ladder subscription-first; no silent metered spill | Issue #13; house credit ladder |
| R13-4 | Do not call non-Gemini LLMs in production until scheduled | Issue #13; plan lane 6 |

Canonical sketch: [`docs/multi-llm-registry.md`](../../docs/multi-llm-registry.md).

---

## Verification (design right)

| Procedure | Expected | Observed | Pass |
|-----------|----------|----------|------|
| V13-1 Registry interface sketch | Protocol + `author_clamped` flow | `docs/multi-llm-registry.md` interface section | **PASS** |
| V13-2 Allowlist names Gemini primary | `gemini-vertex` primary; others parked | Allowlist table | **PASS** |
| V13-3 Clamp ownership named | Points at `clamps.validate_patch` | Sketch + clamps.py exists | **PASS** |
| V13-4 Metered opt-in gate | OpenRouter forbidden without election | Ladder section | **PASS** |
| V13-5 No new prod provider code this wave | No Copilot/Nous/OR client in agent package | Agent still Gemini/ADK + heuristic only | **PASS** |

---

## Validation (right design for the system)

| Procedure | Expected | Observed | Pass |
|-----------|----------|----------|------|
| Val13-1 Wire schema unchanged | schemaVersion 1 only | Sketch requires api-contract | **PASS** |
| Val13-2 Hold / Manual still wins | Stated non-negotiable | Sketch §Non-negotiables | **PASS** |
| Val13-3 Frontend stays keyless | No provider keys in public HTML | Invariant restated; matches api-contract | **PASS** |

---

## Negative controls (design-level)

| Control | Expected | Observed | Pass |
|---------|----------|----------|------|
| N13-1 Silent metered spill | Forbidden in design | Metered requires `ALLOW_METERED_TIER=1` | **PASS** |
| N13-2 Provider bypasses clamps | Forbidden | `author_clamped` → validate_patch only | **PASS** |
| N13-3 Prod non-Gemini call in this wave | Must not land | Sketch + V13-5 | **PASS** |

---

## Design review checklist

- [x] Registry interface documented
- [x] Seat ladder subscription-first
- [x] No production non-Gemini stated
- [x] Same schema + clamps ownership
- [x] Evidence under `.vv/13/`
- [x] Implementation remains future / parked

---

## Promotion note

Design ACs for #13 are **complete**. Impl stays parked. Board Status → Done is owned by **`integrate-deploy-board`**. May defer joint Todo Done until #12 evidence-green if needed.

**Result:** **PASS** (design scope).

## Verify stamp

| Field | Value |
|-------|--------|
| **Ran UTC** | `2026-09-08T00:17:45Z` |
| **Command** | `bash .vv/13/verify.sh` |
| **Result** | OK |
