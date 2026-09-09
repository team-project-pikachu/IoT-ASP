# V&V evidence — Google Nest Device Access integration (#85)

**Configuration item:** `services/autoroute-adk/iot_asp_autoroute/nest/**`, `tests/test_nest_*.py`,
`scripts/nest_gcp_bootstrap.sh`, `scripts/nest_dev.sh`, `scripts/nest_secrets_headless.sh`.
**Revision under test:** branch `claude/google-home-integration-l0zu25` merged with base `main` @ `80b32b5`
(#185, Beam AirPlay headroom; on top of #183, which locks Web Audio gain at 100% and removes the slider).
**Date (UTC):** 2026-09-09. **Operator:** Claude Code session (remote Linux container).
**Secrets:** none read, none present. No values appear in this file.

## Procedure and observed results

| Command | Exit | Last line |
|---------|------|-----------|
| `bash scripts/ci_static_gates.sh` | `0` | `OK ci_static_gates` |
| `bash scripts/nest_dev.sh` | `0` | `OK nest_dev` |
| `bash scripts/autoroute_dev.sh` | `0` | `OK fleet_log jsonl` |
| `python3 scripts/mdc_convert.py --check` | `0` | `OK mdc_convert --check` |
| `bash scripts/nest_gcp_bootstrap.sh` (dry run) | `0` | `OK nest_gcp_bootstrap` |
| `PYTHONPATH=services/autoroute-adk python3 -m pytest tests -q` | `0` | `557 passed in 50.42s` |
| `… pytest tests/test_nest_*.py -q` | `0` | `224 passed in 11.95s` |
| `bash tests/e2e/run.sh` | `0` | `11 passed (10.9s)` / `OK e2e` |
| `bash scripts/nest_secrets_headless.sh check` | **`1`** | `FAIL: op not installed (brew install 1password-cli)` |

The last row is an **expected** non-zero: the container has no `op` binary, and the script is
headless-only by design, so it refuses rather than degrading to an interactive prompt. Re-run on a
host with `op` and `OP_SERVICE_ACCOUNT_TOKEN` exported.

Determinism: the suite was run twice from a cleared `__pycache__` at `e41b32a` — `556 passed` both
times, the second with `-p no:randomly`. The count is `557` in the table above because merging #183
brought its own tests with it. Merging #185 left the count at `557`: it added assertions inside
existing tests rather than new test functions (verified — no `def test_` added or removed in its
diff), and those assertions pin exact literals from its own `public/index.html` changes, so a green
suite is itself proof the merge preserved #185's code verbatim.

Carried from an earlier revision and still the standing explanation: two failures once seen in
`test_nest_poller.py` were traced to a stale bytecode cache left by a branch reset that briefly
removed `poller.py`, not to test-order pollution.

CI on `e41b32a`, the head this branch carried before the #183 merge:
[run 390](https://github.com/team-project-pikachu/IoT-ASP/actions/runs/34303143667) — `success`.
Runs 388 and 389 on that same sha show `cancelled` jobs; both were superseded by 390 under `ci.yml`'s
`concurrency: cancel-in-progress`, after a PR-body edit re-triggered the workflow, and their job logs
cancel inside `setup-python` before any test body ran. Recorded because that pattern reads like
failure and is not — no fix and no re-run were owed.

## Negative controls

A gate that has never failed is not evidence. Each was driven to failure with a planted input, then
the input removed and green confirmed.

Re-verified on `e41b32a`, not inherited from the earlier revision. The first three rows were re-driven
by hand with planted inputs (synthetic placeholder ids, never a real resource name), each observed
`exit 1` with the offending file named, then removed — `OK ci_static_gates`, `exit 0`. The Hold /
Manual, patch-path, patch-field and cadence rows are asserted by `scripts/nest_dev.sh` on every run
(`exit 0` above); quota drift by `ci_static_gates.sh`; PII containment and detector degradation by the
pytest suite.

| Control | Planted input | Observed |
|---------|---------------|----------|
| Nest PII gate | `home.google.com/u/0/home/<64-hex>/devices` and `enterprises/<uuid>/devices/<opaque>` in a tracked file | `FAIL: site-identifying Nest resource in tracked files` — both patterns named; exit `1` |
| Headless-`op` gate | a script containing `eval $(op signin)` and no `OP_SERVICE_ACCOUNT_TOKEN` | `FAIL: interactive-only 1Password auth`; exit `1` |
| Restore | both probes removed | `OK ci_static_gates`; exit `0` |
| Hold / Manual — authoring | `holdManual: true` on a maximal corroborated burst | `(False, 'holdManual — refuse patch')`, patch `{}` |
| Hold / Manual — escalation | confidence `0.99` glass-shatter under Hold | `escalation_hint(...) == {}` |
| Hold / Manual — write | `react()` under Hold with a recording writer | `written=False`, writer **never called** |
| Patch path | `meta/patches/node1.json`, `meta/patches/../telemetry/x.json` | both refused by the guard (`nest_dev.sh`) |
| Patch field on the wire | `vol`, `algo`, `holdManual`, `suddenFreq`, `fMin`, `seedAction`, `priors` | each raises `PatchWriteRefused` |
| Sub-floor cadence | `list_cadence_s=11.999`, camera `< 36.0` | `ValueError` — refused, never silently clamped |
| PII containment | sentinel `previewUrl`, raw device id, `userId` through the mapper | absent from every telemetry value; wire carried `nestDeviceRef` only |
| Quota drift | constants compared to the published table | `nest quotas list=12.0s camera=36.0s maxCameras=6 OK` |
| Detector degradation | engine raises inside `classify_strict` | falls back to `offline_heuristic`, loop unbroken |

## Formal check of the quota property (three independent ways)

1. **Analytic** — floors recomputed from the published numbers: `60/5 = 12.0` s (`devices.list`),
   `3600/100 = 36.0` s (camera instance, the **hourly** cap binding over the per-minute one), and
   `10 QPM ÷ (1/36 s⁻¹) = 6` cameras on the poll path.
2. **Simulation** — a simulated clock driven ≥2 h across a `devices.list` stream plus three cameras,
   requesting greedily as fast as the limiter allows, logging every admitted call.
3. **Independent recomputation** — a standalone checker in the test file recomputes, from that call
   log alone and never from the limiter's internal counters, the count in every trailing 60 s and
   3600 s window and asserts none exceeds quota.

## Not verified here (owner-run, no credentials in this environment)

- Live `gcloud` apply against `bear-iot-asp-rec`; no `gcloud`, no `op`, no GCP credential present.
- **Read-back of the `group:sdm-publisher@googlegroups.com` / `roles/pubsub.publisher` binding.** This
  is the one setting that fails *silently* — a wrong principal delivers zero events forever — so
  `gcloud pubsub topics get-iam-policy` output must be pasted here before this item is called passed.
- End-to-end latency against real hardware; the documented budget is derived, not measured.

**Verdict:** PASS for everything offline and deterministic. **PENDING** for the three live items above.
