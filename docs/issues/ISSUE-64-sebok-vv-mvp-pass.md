# ISSUE-64 — SEBoK V&V MVP pass matrix

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/64  
**Classification:** V&V docs (Balanced PR7 deepen)  
**Status:** matrix software rows → `in_progress` with `.vv/64/SOFTWARE-VERIFY.md` — **pass rows not claimed**

## Did

- Point roadmap V&V pillar at `.vv/matrix.md` (C1–C6 + SCH1 / HOLD1)
- PR7: software verify note; C1/C4/C5/SCH1/HOLD1 → `in_progress` (CI evidence only)
- `tests/test_api_contract.py` locks HTML ↔ RECORD_KEYS ↔ contract tokens

## Didn't

- Mark matrix rows `pass` without fresh evidence packs
- Invent lab / HW results

## Next

- Owner attach evidence packs under `.vv/` after `#62` field run + CI green
- Then flip selected rows to `pass`
