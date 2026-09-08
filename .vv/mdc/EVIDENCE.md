# `.vv/mdc` — Cursor `.mdc` → Claude Code conversion evidence

**Config item:** `scripts/mdc_convert.py`, `.mdc-convert.json`, `CLAUDE.md`, `.claude/rules/*.md`, CI job `mdc check`
**Docs:** `docs/mdc-conversion.md`
**Date:** 2026-09-08 (UTC)

## Requirements

| ID | Requirement |
|----|-------------|
| MDC-01 | Parse Cursor frontmatter (`description`, `globs`, `alwaysApply`) incl. non-YAML `globs: *.ts, **/*.tsx` |
| MDC-02 | Map Always / Auto Attached / Agent Requested / Manual per the cursor.com/docs/rules table |
| MDC-03 | Emit `.claude/rules/<slug>.md` with `paths:` frontmatter (code.claude.com/docs/en/memory) |
| MDC-04 | Emit `.claude/skills/<slug>/SKILL.md` with `name` + `description` |
| MDC-05 | Managed blocks in `CLAUDE.md` / `SPEC.md`; hand-written text preserved |
| MDC-06 | Idempotent; `--check` exit 1 when stale; pruning of removed sources |
| MDC-07 | Nested `.cursor/rules` scoping; external `--src` dirs; slug collisions deterministic |
| MDC-08 | Stdlib only; runs on Python 3.11 (local) and 3.12 (CI) |

## Procedure

```bash
python3 -m pytest tests/test_mdc_convert.py -q
python3 scripts/mdc_convert.py --check
python3 scripts/mdc_convert.py --dry-run --json
```

## Observed

| Check | Result |
|-------|--------|
| `pytest tests/test_mdc_convert.py` | exit 0 — **22 passed** (0.21 s) |
| `mdc_convert.py --check` on this repo | exit 0 — four `.mdc` sources mapped; outputs up to date |
| `--dry-run --json` | Covered by the converter fixture tests; no write was performed by this evidence run |

## Pass/fail

| Req | Status |
|-----|--------|
| MDC-01 … MDC-08 | **PASS** (unit + fixture-repo tests) |

## Pending on the Mac

Run `python3 scripts/mdc_convert.py` (optionally `--src ../.cursor/rules`) in `/Users/machine/apps/IoT-ASP`,
commit `.cursor/rules/*.mdc` plus generated outputs; the `mdc check` CI job then enforces freshness.
