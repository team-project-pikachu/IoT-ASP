# Evidence package — Issue #12 (Gemini autoroute)

**Status:** Phase 1 matrix scaffold + GREEN lane draft package (see siblings).  
**Issue:** [#12](https://github.com/team-project-pikachu/IoT-ASP/issues/12)

## Index

| Artifact | Path |
|----------|------|
| Package README | [README.md](README.md) |
| Requirements | [requirements.md](requirements.md) |
| Procedures | [procedure.md](procedure.md) |
| Observed results | [observed-results.md](observed-results.md) |
| Negative controls | [negative-controls.md](negative-controls.md) |
| Dry-run fingerprint | [dry-run-patch-fingerprint.txt](dry-run-patch-fingerprint.txt) |
| Matrix rows | [../matrix.md](../matrix.md) (`I12-*`, C1–C6, SCH1, HOLD1) |

## Known drift (integrate / fix lane)

- `scripts/autoroute_dev.sh` historically asserted old vol refuse vs `clamps.py` `vol_hard_max=100` (C4) — confirm fixed in observed-results before Project Done.
- Missing `docs/gcp-recordings.md` (ops narrative; not blocking #12 code).

## Promotion

Project Status → Done only after integrate lane: fresh evidence + production HTTP 200 as required by matrix.
