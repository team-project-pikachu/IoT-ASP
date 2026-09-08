# #24 — Deps: migrate `google-adk` / `google-genai` to 2.x (breaking)

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/24 · Labels: `enhancement`, `parked` · Related: [27-continuous-ship-dev-test-prod.md](27-continuous-ship-dev-test-prod.md) (CI installs `requirements.txt`), `docs/adk-autoroute.md`

## Status

**Parked — keep `google-adk` major 1 (`<2`).** Production `services/autoroute-adk/requirements.txt` already pins `google-adk>=1.39.1,<2` and `google-genai>=2.22.0,<3`. The genai major-2 pin is **required** by `google-adk>=1.36` (PyPI metadata `google-genai>=2.9,<3`); it is not the #24 migration. `.claude/rules/autoroute-backend.md:19` still says keep both `<2` — the genai half is stale vs the manifest. This spec lists the **concrete ADK 2.x breaking changes that touch our `LlmAgent` / `root_agent`**, what does *not* touch us, the migration steps, and the acceptance gates — so unparking is a bounded change, not a research task.

No production pin changes with this spec. Parked 2.x **targets** live only in `services/autoroute-adk/requirements-adk2.example.txt`.

Versions on 2026-09-08 (PyPI, via Firecrawl): `google-adk` **2.8.0** (2026-08-26; 2.0.0 GA 2026-05-19;
latest 1.x **1.39.1**, 2026-08-27 — the 1.x line is still maintained) · `google-genai` **2.22.0**
(2026-09-02; 2.0.0 2026-05-07; last 1.x **1.75.0**, 2026-05-04).

Honesty pass (this revision, `origin/main` @ `2ca7501`): acceptance is the **named** `root_agent` tool set, not a frozen integer count. `#29` / `#25` / `#26` added `fleet_log_summary`, `live_features`, and `hw_limits_report` after an earlier draft froze a 7-tool list.

## Goal

Move the autoroute backend to `google-adk>=2.8,<3` (and keep `google-genai>=2.22,<3`) **without** changing the
wire contract, the clamps, the dry-run path, or the frontend — and with an import smoke that proves
`iot_asp_autoroute.agent.root_agent` still loads and exposes **exactly these named tools** (order as in `agent.py`):

`read_telemetry`, `write_patch`, `list_safety_clamps`, `seismo_acoustic_priors`, `colab_handoff_note`, `ingest_telemetry`, `process_sudden_freq`, `fleet_log_summary`, `live_features`, `hw_limits_report`.

Do not freeze a raw integer in the unpark test; assert the name set (and, when wrapping preserves order, the sequence). Adding or renaming a tool is a spec change, not a silent count bump.

## Prior art

Searched in the order `CLAUDE.md` → Working conventions (2026-09-08 UTC). Register row in `docs/PRIOR_ART.md`.

1. **This repo** (`rg google-adk|LlmAgent|root_agent`, `git log -S google-adk --all`, `origin/main` @ `2ca7501`): `services/autoroute-adk/requirements.txt` already holds the parked 1.x ADK pin and the required genai 2.x pin; `requirements-adk2.example.txt` already holds the unpark target (`google-adk>=2.8.0,<3`); `agent.py` is a single `LlmAgent` with ten plain callables (no `FunctionTool` wrappers in source, no `BaseAgent` subclass, no `Runner`, no session service). `docs/dependencies.md` and `docs/mvp-tooling.md` already record "do not force ADK 2.x". **Reuse:** keep the constructor shape; do not write a custom migrator.
2. **Owner's Mac clone** (issue #24 body + comments): the issue body still lists genai `>=1.75.0,<2`; a 2026-09-08 comment records that genai **did** move to `>=2.22.0,<3` because ADK 1.36+ requires it. The remaining parked work is **ADK major 2 only**. Tool list on the clone matches `origin/main` (same ten names). **Decision:** docs honesty only; do not bump `google-adk`.
3. **Org repos** (`gh search code org:team-project-pikachu google-adk LlmAgent`): hits are this repository only (spec, deps docs, `.vv/deps/`, `agent.py`). No sibling autoroute agent to copy a 2.x port from.
4. **awesome-lists** (topic `awesome-list` / awesome-python / awesome-gemini): no maintained ADK 1→2 code migrator. Google's own `adk migrate session` upgrades **session DB** schema to `"2.0"` — we have no session store.
5. **Context7 / Firecrawl** — `/google/adk-python` README "BREAKING CHANGES FROM 1.x" (agent API, event model, session schema; 2.0 sessions readable by ADK ≥ 1.28); `adk migrate session`; optional `App(name=…, root_agent=…)` container; `LlmAgent(name, model, description, instruction, tools=[callables])` still the documented constructor in 2.x samples. **Decision: park.** Unparking is a pin bump + import smoke + optional `App` export, not a new package.

## Shipped on `main`

Verified by reading the files on `origin/main` @ `2ca7501` (this branch):

| What | Where |
|------|-------|
| Pins `google-adk>=1.39.1,<2`, `google-cloud-storage>=3.13.0,<4`, `google-genai>=2.22.0,<3` | `services/autoroute-adk/requirements.txt:5-7` |
| Parked 2.x **example** pins (`google-adk>=2.8.0,<3`, `google-genai>=2.22.0,<3`) — not installed | `services/autoroute-adk/requirements-adk2.example.txt` |
| `from google.adk.agents import LlmAgent` inside `try/except ImportError` (the only ADK import in the package) | `services/autoroute-adk/iot_asp_autoroute/agent.py:9-15` |
| `root_agent = LlmAgent(name="iot_asp_autoroute", description=…, instruction=INSTRUCTION, tools=[10 named callables])` | `agent.py:53-70` |
| Tools are plain Python functions (`read_telemetry`, `write_patch`, `list_safety_clamps`, `seismo_acoustic_priors`, `colab_handoff_note`, `ingest_telemetry`, `process_sudden_freq`, `fleet_log_summary`, `live_features`, `hw_limits_report`) — no `FunctionTool`, no `BaseAgent` subclass, no session-service code, no `Runner` usage | `services/autoroute-adk/iot_asp_autoroute/tools.py`; `grep -rn "Runner\|BaseAgent\|SessionService\|_run_async_impl" services/` → nothing |
| No direct `google.genai` import anywhere (`grep -rn "google.genai\|from google import genai" services/` → nothing); only `google.cloud.storage` and `google.api_core` | `gcs_io.py`, `features_live.py`, `fleet_log.py` |
| Package importable without ADK (`__init__.py` soft-fails `agent`); dry-run `scripts/autoroute_dev.sh` uses only stdlib + numpy/scipy | `iot_asp_autoroute/__init__.py`; `CLAUDE.md` § Toolchain; `.claude/rules/autoroute-backend.md:10` |
| CI `tests` job does **not** install `google-adk` (`requirements-dev.txt` only). `autoroute` job installs `requirements.txt` and runs an import smoke for clamps / sudden_freq / Hold refuse | `docs/ci.md`; `.github/workflows/ci.yml` |
| Deploy commands `adk deploy agent_engine` / `adk deploy cloud_run` with `--project`, `--region`, `--display_name` / `--service_name` | `docs/adk-autoroute.md:98-115` |
| Parked-spec name lock: AST parse of `agent.py` `tools=[…]` plus skip-unless-ADK live import | `tests/test_agent_import.py` |

## Remaining scope — ADK 2.x breaking changes and how they land here

Source for each row is in *Sources* (Context7 `/google/adk-python` README + `v2.6.1`, adk.dev 2.0 page).

| # | ADK 2.0 change | Touches us? | Action when unparked |
|---|----------------|-------------|----------------------|
| 1 | **Workflow Runtime**: hierarchical executor → graph engine; `BaseAgent` → nodes (`BaseNode`); custom overrides of `_run_async_impl()` / `generate_content()` are **silently bypassed**; inject logic via `BeforeAgentCallback` / `AfterAgentCallback` | No (we subclass nothing) | Add a negative control test: `agent.py` contains no `class … (BaseAgent)` / `_run_async_impl`. |
| 2 | **Event schema** gains `node_info` and `output` (Python; TS/Go add `route`/`isolationScope`/`requestedInput`); 2.0 sessions readable only by ADK ≥ 1.28; DB session stores need `adk migrate session` to schema `"2.0"` | Not today (no session service, no DB) | If a persistent session service is ever added, run `adk migrate session`; until then, none. |
| 3 | **In-place mutation forbidden**: never `context.session.events.append(...)`, never `enqueue_event` directly | No | Lint grep in the smoke test. |
| 4 | **Error handling**: let exceptions propagate to `RetryConfig(max_attempts=N)`; never catch `BaseException` in tools | Partially — tools return `{ok: False, …}` dicts rather than raising | Keep the dict contract (it is our API to the model) but ensure no `except BaseException` / bare `except:` in `tools.py`. |
| 5 | `SequentialAgent` / `ParallelAgent` / `LoopAgent` deprecated in favour of `Workflow` (`Workflow` cannot be an `LlmAgent` sub-agent; use Workflow-as-Tool) | No | None. |
| 6 | **`App` container** (`from google.adk.apps.app import App`; `App(name=…, root_agent=root_agent)`) wraps the root agent for plugins, compaction, context caching; `from google.adk import Agent` remains an alias | Optional | Export `app = App(name="iot_asp_autoroute", root_agent=root_agent)` next to `root_agent` (additive; `adk deploy` still accepts the package). |
| 7 | `LlmAgent(name, model, description, instruction, tools=[callables])` — same constructor shape in `v2.6.1` samples (`AgentTool` example, `App` example) | Compatible as written | Import smoke only. |
| 8 | `McpToolset` replaces all-caps `MCPToolset` | No (no MCP tools) | None. |
| 9 | `google-genai` 2.x major (ADK 2.x depends on it) | Indirect only — no direct import; **already pinned** `>=2.22.0,<3` on main | Leave the genai pin; do not regress it when bumping ADK. |
| 10 | Python floor: ADK 2.x wheels target current Python 3.x; CI already runs 3.12 | No | Keep 3.11 locally / 3.12 CI; verify the wheel's `Requires-Python` at bump time. |

Steps (one PR, `Fixes #24` — **not this parked-spec PR**):

1. `requirements.txt`: `google-adk>=2.8.0,<3` (copy from `requirements-adk2.example.txt`). Keep `google-genai>=2.22.0,<3` (already on main) and `google-cloud-storage` as is.
2. `agent.py`: keep `LlmAgent`; add the optional `app = App(...)` export inside the same `try` block
   (`from google.adk.apps.app import App`), so the module still raises the friendly `ImportError` without ADK.
3. `tests/test_agent_import.py` (skips the live import when ADK is not installed): `root_agent.name == "iot_asp_autoroute"`,
   tool **names** equal `EXPECTED_ROOT_AGENT_TOOL_NAMES` (the ten callables above); negative controls from rows 1, 3, 4.
4. CI `autoroute` job: after `pip install -r services/autoroute-adk/requirements.txt`, run
   `python -c "import iot_asp_autoroute.agent as a; assert a.root_agent"` (already the import-smoke step;
   confirm it executes with ADK 2.x installed) and keep the ADK-less dry-run step first.
5. Re-run `adk deploy cloud_run … --service_name=iot-asp-autoroute-adk` on a preview service; record
   `.vv/deps/adk-2x.md` (commands, exit codes, no secrets). `docs/dependencies.md` gets
   the audit row when the bump lands.

## Wire fields

None. `schemaVersion: 1` and every telemetry/patch field are untouched by an SDK bump; the ADK is not on
the wire (frontend never sees it — `docs/api-contract.md` invariant 1).

## Clamps / safety

- Clamps (`clamps.py`) and `tools.write_patch` re-validation are pure Python; they do not change.
- Hold / Manual refusal lives in `tools._latest_hold_manual` / `write_patch`, independent of ADK.
- Dry-run (`scripts/autoroute_dev.sh`) must stay green **without** ADK installed (rule
  `.claude/rules/autoroute-backend.md:10`).
- Secrets by name only (`GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `IOT_ASP_GCS_BUCKET`); ADC for deploys.
- No frontend change, no Vercel redeploy (`CLAUDE.md` invariant 11).

## Acceptance tests

(From the issue's checklist, made concrete.)

1. `python3 -m pytest tests/test_agent_import.py -q` passes with `google-adk>=2.8` installed
   (`root_agent` loads; named tool set matches `EXPECTED_ROOT_AGENT_TOOL_NAMES`; `app.root_agent is root_agent` if the `App` export is added).
2. The live-import test is **skipped**, not failed, when `google.adk` is absent (`pytest.importorskip`). The AST name parse always runs (CI `tests` job does not install ADK).
3. `bash scripts/autoroute_dev.sh` → exit 0 in an environment **without** ADK.
4. Negative controls: `grep -n "_run_async_impl\|session.events.append\|enqueue_event\|except BaseException" services/autoroute-adk` → empty.
5. Until unparked: `requirements.txt` has exactly one `google-adk` line and it satisfies `>=1.39.1,<2`; `google-genai` stays `>=2.22.0,<3`. After unpark: the `google-adk` line satisfies `>=2.8.0,<3`.
6. `docs/adk-autoroute.md` deploy commands still work verbatim (`adk deploy agent_engine|cloud_run` exist in 2.x — verified in `v2.6.1` samples).
7. Evidence file `.vv/deps/adk-2x.md` lists the CI run URL and the preview `adk deploy` exit code (unpark PR only).

## CI gate

- `autoroute` job (installs `requirements.txt`, dry-run, import smoke) is the gate; the drift assertion
  `vol_hard_max == 100` runs first and is unrelated to the SDK.
- `tests` job picks up `tests/test_agent_import.py` without installing ADK — source name parse + parked-pin guard run; live import skips.
- Until unparked, the guard in `tests/test_agent_import.py` asserts the **current** `google-adk` pin (`<2`) so an accidental bump fails loudly; it is removed or inverted in the migration PR.

## Risks / HW limits

- ADK 2.x is a runtime rewrite (graph engine); even though our code is a plain `LlmAgent` with function
  tools, model/tool-call behaviour (retries, event streaming) changes under the hood. Validate with a
  preview Cloud Run service before touching production.
- `google-genai` 2.x may change response/`types` shapes; we do not import it, but ADK's tool-call plumbing
  does — the import smoke plus a live preview call are the only real checks. Genai 2.x is already the
  install on main, so that particular major is not new work for #24.
- The 1.x line is still receiving releases (1.39.1 on 2026-08-27), so staying parked has no immediate
  security cost; the cost is drift relative to docs and samples that now assume 2.x.
- Agent Engine / Cloud Run images pin their own Python; check `Requires-Python` of the chosen wheel.

## Sources

- Context7 `/google/adk-python` (README, "Agent Development Kit (ADK) 2.0 > Breaking Changes from 1.x":
  agent API, event model, session schema; 2.0 sessions readable by ADK 1.28+; `sessions/migration/README.md`
  schema version `"2.0"`, `adk migrate session`; `McpToolset` replaces `MCPToolset`).
- Context7 `/google/adk-python/v2.6.1` (`contributing/samples/core/app/README.md`: `App(name=…, root_agent=…)`,
  `from google.adk import Agent`; `docs/guides/agents/managed_agent`: `LlmAgent(name, description, tools=[AgentTool(...)])`;
  `Runner.run_async` yields `Event`; `Session` fields `id, app_name, user_id, state, events, last_update_time`;
  `adk deploy agent_engine` / `adk deploy cloud_run` samples).
- Firecrawl developer search → adk-docs `docs/2.0/index.md` ("ADK Python 1.x compatibility": Workflow
  Runtime / `BaseAgent`→`BaseNode`, bypassed `_run_async_impl`, `BeforeAgentCallback`/`AfterAgentCallback`,
  no `context.session.events.append`, `RetryConfig(max_attempts=3)`, never catch `BaseException`);
  adk.dev `llms-full.txt` (Event gains `node_info` and `output`; do not use `enqueue_event`);
  adk-docs issues #2185 / #2190 (`SequentialAgent`/`ParallelAgent`/`LoopAgent` deprecated → `Workflow`;
  per-language Event field lists).
- Firecrawl search → PyPI https://pypi.org/project/google-adk/ (2.8.0 2026-08-26; 2.0.0 2026-05-19; 1.39.1
  2026-08-27) and https://pypi.org/project/google-genai/ (2.22.0 2026-09-02; 2.0.0 2026-05-07; 1.75.0 2026-05-04).
- GitHub issue #24 (read via the GitHub connector, 2026-09-08) — acceptance checklist + comments that genai 2.x already landed and that a 7-tool count was stale.
- Repo: `services/autoroute-adk/requirements.txt`, `requirements-adk2.example.txt`, `agent.py`, `tools.py`, `.claude/rules/autoroute-backend.md:19`,
  `docs/adk-autoroute.md`, `docs/ci.md`, `docs/dependencies.md`.
