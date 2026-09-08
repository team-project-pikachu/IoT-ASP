# ISSUE-24 — google-adk / google-genai 2.x

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/24  
**Classification:** parked (spec honesty pass)  
**Owner surface:** backend  
**Canonical spec / ADR:** `docs/specs/24-adk-2x-migration.md`

## Scope (this pass)

Keep `google-adk` major 1 on `main`. Make the parked spec match `origin/main` `root_agent.tools` (named list, not a stale 7-tool count). `google-genai` is already `>=2.22.0,<3` (required by `google-adk>=1.36`).

## Constraints

- No site PII in public docs.
- Do not invent secrets, entitlements, or HW capabilities.
- Prefer linking existing `docs/specs/` over forking tables (`docs/api-contract.md` is wire canon).
- Do not bump production `requirements.txt` to `google-adk` 2.x.
- Do not rewrite `agent.py`.
- Hold / Manual and `schemaVersion: 1` untouched.

## Did

- Corrected `docs/specs/24-adk-2x-migration.md`: ten named tools on `origin/main` (`read_telemetry`, `write_patch`, `list_safety_clamps`, `seismo_acoustic_priors`, `colab_handoff_note`, `ingest_telemetry`, `process_sudden_freq`, `fleet_log_summary`, `live_features`, `hw_limits_report`).
- Added `## Prior art` (repo convention) and a `docs/PRIOR_ART.md` register row.
- Documented current pins vs parked example: `google-adk>=1.39.1,<2` stays; `google-genai>=2.22.0,<3` already on main; `requirements-adk2.example.txt` remains the 2.x target.
- `tests/test_agent_import.py`: AST name parse always runs; live `root_agent` import skipped unless ADK is installed; parked `<2` pin guard. CI `tests` job does not install `google-adk`.

## Didn't

- Did not bump `services/autoroute-adk/requirements.txt` to `google-adk` 2.x.
- Did not rewrite `agent.py` or the registered tool list.
- Did not unpark, deploy, or add `.vv/deps/adk-2x.md`.

## Next

- Unpark only with import smoke against ADK 2.x using `EXPECTED_ROOT_AGENT_TOOL_NAMES` (not a frozen integer).
- Keep dry-run (`scripts/autoroute_dev.sh`) stdlib-safe without ADK.
- Optional `App(...)` export is additive when unparking.
