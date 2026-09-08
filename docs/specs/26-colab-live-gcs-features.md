# #26 — Colab live GCS: accel / gyro / micDiff telemetry → `meta/features`

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/26 (parent #17, milestone M3)
Owned files: `services/autoroute-adk/iot_asp_autoroute/features_live.py`, `tests/test_features_live.py`,
`notebooks/iot_asp_colab_etl.md`, `notebooks/iot_asp_colab_etl.ipynb`, `.vv/colab-sensors.md`, this spec.

## Status

**Implemented 2026-09-08 on branch `claude/mdc-conversion-features-gu3yzk` (not yet on `main`).**
`features_live.py`, `tests/test_features_live.py` (26 tests, FL-01 … FL-13), the regenerated notebook
pair and `.vv/colab-sensors.md` are on the branch; the offline path (dry-run mirror) is fully tested in
CI. The live GCS write is gated behind Colab `userdata` names and is recorded as `live: PENDING` in
`.vv/colab-sensors.md` until an owner runs the notebook with `LIVE_GCS=1`.

### Implemented on the branch (differences from the plan below)

| What | Where |
|------|-------|
| Constants `SENSOR_COLUMNS` (18), `ALL_COLUMNS`, `MIC_DIFF_ALPHA`, band thresholds, prefixes | `features_live.py` "constants" block |
| `mic_diff`, `band_burst`, `project_sensor_features`, `normalize_ts` (ISO / epoch s / epoch ms / `T00-00-05Z` object-name style) | `features_live.py` "pure helpers" |
| `parse_telemetry_objects(names, reader=None, text_reader=None, errors=None)` — `errors` is an optional list that collects `{object, line, error}` for skipped lines (the plan said "counted in `errors`"; a list keeps the function pure) | `features_live.py` |
| `list_telemetry_names(node)` (dry-run adds `*.jsonl` glob, dedupes) + `latest_points(node, limit)` | `features_live.py` |
| `build_feature_record` also adds `sampleHz` and `sourceObjects` (sorted source names) — additive | `features_live.py` |
| `run_live` result adds `written` and `shriekBias` next to the planned keys; explicit `live=True` without `IOT_ASP_GCS_BUCKET` is **downgraded** to the dry-run mirror | `features_live.py` |
| Live mode forces `gcs_io.DRY_RUN = False` and refreshes `gcs_io.BUCKET` from env for the duration (reads + write), restored afterwards; non-live forces `DRY_RUN = True` | `features_live._gcs_mode` |
| `demo_points(node, n, seed)` (pure) feeds `_seed_demo`; point 9 carries `soundBurst=True`, `micEnergy=-20` | `features_live.py` |
| Notebook cell 3 (`from iot_asp_autoroute import features_live`) seeds the mirror with `_seed_demo` when **not** live so the notebook runs offline end-to-end | `notebooks/iot_asp_colab_etl.*` |
| FL-12 additionally asserts the `.md` python fences equal the `.ipynb` code-cell sources (generated from one cell list) | `tests/test_features_live.py` |
| FL-09 live branch stubs `features_live.latest_points` so no GCS client is constructed; asserts `gcs_io.DRY_RUN`/`BUCKET` are restored | `tests/test_features_live.py` |

## Goal

Extend (never modify) the shared Colab/ADK ETL so that telemetry heartbeats carrying phone
**accelerometer / gyroscope / mic-spectrum** sensor fields (`ax..gz`, `accelAxes`, `gyroAxes`,
`outLevel`, `micDiff`, `bandBurst`, `soundBurst`, `extremeActive`, `lfEnergy`, `usEnergy`, …) are
projected into a **features** object under `meta/features/<deviceId>/<ts>.json`, computed from the last
`limit` telemetry points (objects or JSONL), with a `shriekBias` hint for the patch author. The module is
runnable offline (`--seed-demo`) and from Colab with secrets referenced **by name only**. It never writes
`meta/patches/` (Colab/ETL is never authoritative — CLAUDE.md "Storage" cheat-sheet and
`.claude/rules/autoroute-backend.md`).

## Shipped on `main`

Verified by reading the code at branch head `0625e91`:

| What | Where |
|------|-------|
| Telemetry feature columns (`TELEMETRY_FEATURE_COLUMNS`) — the base tuple `ALL_COLUMNS` extends | `services/autoroute-adk/iot_asp_autoroute/colab_etl.py:26-58` |
| `normalize_telemetry()` aliases `a`→`absA`, `ctxState`→`audioContextState`, vol → UI percent | `colab_etl.py:66-91` |
| `extract_features(telemetry, *, vib_series, engine_id)` → `{schemaVersion, kind:"iot_asp_features", deviceId, ts, engineId, telemetry, derived, anomaly, credentialPolicy}` | `colab_etl.py:119-171` |
| `SAMPLE_HZ = 1.0`, `ENGINE_ID_DEFAULT = "iot-asp-autoroute"` | `colab_etl.py:62-63` |
| `sample_telemetry_fixture()` (no sensor columns yet) | `colab_etl.py:208-240` |
| Authoritative vib anomaly: `detect_disturbances()` (SciPy medfilt + MAD + find_peaks, 0.0005 g quantum) | `vib_anomaly.py:50-149`, `VIB_QUANTUM` at `vib_anomaly.py:24` |
| `detect_from_telemetry_points()` picks `vib` → `vibQ` → `absA` → `a` per point | `vib_anomaly.py:164-182` |
| `synthetic_demo_series(n, seed)` seeded 1 Hz demo series | `vib_anomaly.py:152-161` |
| Storage adapter: `DRY_RUN`, `DRY_ROOT` (env `IOT_ASP_AUTOROUTE_DRY_ROOT`), `is_dry_run()` | `gcs_io.py:12-22` |
| `write_json()` returns `file://…` in dry-run else `gs://<bucket>/<object>` | `gcs_io.py:31-42` |
| `read_json()`, `list_prefix()` (dry-run `rglob("*.json")` — **does not list `.jsonl`**) | `gcs_io.py:45-73` |
| Ingest writes `meta/telemetry/<node>/<ts>.json` with `:`→`-` in the object name | `tools.py:144-152` |
| `read_telemetry()` takes `names[-1]` of `list_prefix` (lexicographic, not ts-parsed) | `tools.py:20-35` |
| `colab_handoff_note()` writes `meta/colab-jobs/<node>-latest.json`, points at the notebook | `tools.py:98-121` |
| `is_sudden_freq_event()` (holdManual short-circuit) | `sudden_freq.py:42-53` |
| Existing Colab stub: reads `GCP_SA_JSON` / `IOT_ASP_GCS_BUCKET` from `userdata`, only sketches features | `notebooks/iot_asp_colab_etl.md:4-47`, `.ipynb` cells 0-2 |
| Pipeline doc naming the userdata secrets by name | `docs/colab-gemini-pipeline.md:26-33` |

Not on `main`: no `features_live.py`, no `tests/` for it (`tests/` is empty), no `.vv/colab-sensors.md`,
no sensor columns in `docs/api-contract.md`, and `public/index.html` on `origin/main` does not yet emit
`micDiff` / `bandBurst` / `soundBurst` / `extremeActive` (`grep` returns nothing; the issue says the
owner's Mac frontend is ahead — treat the fields as additive optional telemetry).

## Remaining scope

### `services/autoroute-adk/iot_asp_autoroute/features_live.py` (new; stdlib + `colab_etl`/`vib_anomaly` imports only)

Constants

```python
SENSOR_COLUMNS = ('ax','ay','az','gx','gy','gz','accelAxes','gyroAxes','outLevel','micDiff',
                  'bandBurst','soundBurst','extremeActive','lfEnergy','usEnergy',
                  'lastHopAgeMs','ctxResumes','watchdogTrips')
ALL_COLUMNS = TELEMETRY_FEATURE_COLUMNS + SENSOR_COLUMNS
MIC_DIFF_ALPHA = 0.85
BAND_LF_THR_DB = -60.0
BAND_US_THR_DB = -55.0
SHRIEK_MIC_DIFF_DB = 6.0
FEATURES_PREFIX = "meta/features/"
FORBIDDEN_PREFIX = "meta/patches"
```

Functions (all pure except `run_live`, `_seed_demo`)

| Function | Contract |
|----------|----------|
| `mic_diff(mic_energy, out_level, alpha=MIC_DIFF_ALPHA, given=None) -> float` | If `given` (the telemetry's own `micDiff`) is a finite number, return it **unchanged**. Else `mic_diff = float(mic_energy) - alpha * float(out_level)`; non-numeric / `None` inputs coerce to `0.0`. Returned as `float`, rounded to 3 dp. |
| `band_burst(lf_energy, us_energy, lf_thr=-60.0, us_thr=-55.0) -> str \| None` | `'both'` if `lf ≥ lf_thr and us ≥ us_thr`; `'lf'` if only LF; `'us'` if only US; `None` when neither crosses or both inputs are `None`/non-numeric. A pre-existing `bandBurst` value in `{'lf','us','both'}` is passed through by `project_sensor_features`. |
| `project_sensor_features(t) -> dict` | Returns only the `SENSOR_COLUMNS` present in `t` (skips `None`). Scalars coerced to `float` (bools `soundBurst`, `extremeActive` stay `bool`; `bandBurst` stays `str` if in the allowed set, else dropped; `ctxResumes`, `watchdogTrips`, `lastHopAgeMs` → `int`). `accelAxes` / `gyroAxes` must be a 3-element sequence → `list[float]` of length 3, else dropped. If `ax,ay,az` are present and `accelAxes` is absent, `accelAxes` is synthesised (same for `gx,gy,gz` → `gyroAxes`). Unknown keys ignored. |
| `parse_telemetry_objects(names, reader=gcs_io.read_json, text_reader=None) -> list[dict]` | Accepts object names under `meta/telemetry/<node>/`. `*.json` → one point; `*.jsonl` → one point per non-blank line (bad lines skipped, counted in `errors`). Every point is `colab_etl.normalize_telemetry`'d; `ts` may be ISO-8601 or epoch ms (ms → `%Y-%m-%dT%H:%M:%SZ`). Result sorted by `ts` ascending, stable on name. |
| `latest_points(node, limit=200) -> list[dict]` | `gcs_io.list_prefix(f"meta/telemetry/{node}/")` **plus** `.jsonl` siblings (dry-run: extra `rglob("*.jsonl")` under `DRY_ROOT`; live: names already come from `list_blobs`) → `parse_telemetry_objects` → keep the last `limit`. |
| `build_feature_record(points, node) -> dict` | Requires `points` non-empty (else `ValueError`). `latest = points[-1]`; `vib_series = [absA or a]` over all points (1 Hz, `SAMPLE_HZ`), skipping points without either key. Calls `colab_etl.extract_features(latest, vib_series=vib_series)` and **adds** additive keys: `sensors` (projected latest sensors; `micDiff` computed via `mic_diff(micEnergy, outLevel)` when absent and `micEnergy`+`outLevel` present; `bandBurst` computed via `band_burst(lfEnergy, usEnergy)` when absent), `shriekBias` (bool: `soundBurst is True or extremeActive is True or micDiff > 6.0`), `sourceCount = len(points)`, `live` (bool set by caller, default `False`), `sensorColumns = list(SENSOR_COLUMNS)`, `micDiffAlpha = 0.85`, `writer = "iot_asp_autoroute.features_live"`. `kind` stays `"iot_asp_features"`; `schemaVersion` stays `1`. |
| `features_object_name(node, ts) -> str` | `f"meta/features/{node}/{ts.replace(':', '-')}.json"`. |
| `assert_not_patch_path(object_name)` | `raise ValueError("refuse: features_live never writes meta/patches")` if `object_name.lstrip('/').startswith("meta/patches")`. Called by `run_live` before every write. |
| `run_live(node, limit=200, write=True, live=None) -> dict` | `live` defaults to `os.environ.get("LIVE_GCS") == "1" and bool(os.environ.get("IOT_ASP_GCS_BUCKET"))`. When `live` is `False` the write is forced to the dry-run mirror (`gcs_io.DRY_RUN = True` for the duration; restored after). Reads `latest_points`, builds the record with `record["live"] = live`, computes `name = features_object_name(node, record["ts"])`, `assert_not_patch_path(name)`, writes via `gcs_io.write_json` iff `write`. Returns `{ "ok": bool, "uri": str \| None, "node", "live", "sourceCount", "featureKeys": sorted(record.keys()), "object": name }`; when no telemetry: `{"ok": False, "error": "no telemetry under meta/telemetry/<node>/", ...}` and no write. |
| `_seed_demo(node, n=12, seed=26) -> list[str]` | Writes `n` synthetic points `meta/telemetry/<node>/2026-09-08T00-00-<ss>Z.json` (1 s apart, fixed base ts) to the dry-run mirror via `gcs_io.write_json`: `ax..gz` from `random.Random(seed)`, `absA` from `vib_anomaly.synthetic_demo_series(n, seed)`, `outLevel=-30.0`, `micEnergy=-40.0`, `lfEnergy=-70.0`, `usEnergy=-50.0`, `algo="hop"`, `suddenFreq=False`, `holdManual=False`; point index 9 has `soundBurst=True`, `micEnergy=-20.0`. Returns written URIs. |
| CLI `python3 -m iot_asp_autoroute.features_live --node node1 --limit 50 [--live] [--seed-demo]` | `--seed-demo` runs `_seed_demo` first; without `--live` the run is dry-run regardless of env. Prints one JSON line (the `run_live` result) and exits 0 on `ok`, 2 otherwise. Never prints env values. |

### Notebook `notebooks/iot_asp_colab_etl.md` + `.ipynb` (kept in sync; `.ipynb` is nbformat 4 JSON with `cells`, `metadata`, `nbformat: 4`, `nbformat_minor`)

Cells, in order:

1. Markdown header: public, no PII, secrets by name only.
2. Code — `userdata` **names** only: `GCP_SA_JSON`, `IOT_ASP_GCS_BUCKET`, `LIVE_GCS`. Exports
   `IOT_ASP_GCS_BUCKET` / `LIVE_GCS` to `os.environ`; writes `GCP_SA_JSON` to a `tempfile` and sets
   `GOOGLE_APPLICATION_CREDENTIALS` to that path (value never printed). Prints only `bucket set: True/False`, `live: 0/1`.
3. Code — `pip install` from the repo (`git clone` + `pip install -e services/autoroute-adk`) **or**
   `sys.path.insert(0, ".../services/autoroute-adk")`.
4. Code — `from iot_asp_autoroute import features_live`; `res = features_live.run_live(NODE, LIMIT, live=os.environ.get("LIVE_GCS") == "1")`.
5. Markdown — "This notebook never writes `meta/patches/`; the ADK worker clamps and writes patches."
6. Code — `print(res["uri"], res["sourceCount"], res["live"])`.

The existing stub `latest_telemetry` / `vib_features` cells are replaced (the shared module is
authoritative; `.claude/rules/autoroute-backend.md` forbids re-implementing detection in notebooks).

### `.vv/colab-sensors.md`

Config item, UTC date, procedure (`python3 -m iot_asp_autoroute.features_live --node node1 --limit 50 --seed-demo`),
observed output with `file://` URIs and exit code, the exact live command
(`LIVE_GCS=1 IOT_ASP_GCS_BUCKET=<name> python3 -m iot_asp_autoroute.features_live --node node1 --limit 200 --live`),
and the line `live: PENDING — requires Colab userdata GCP_SA_JSON + IOT_ASP_GCS_BUCKET + LIVE_GCS=1`.
No secret values, no `gs://` bucket names.

### Integration requests (not owned here)

- `tools.py`: `def live_features(node_id: str, limit: int = 200) -> dict` wrapping `features_live.run_live(node_id, limit)` (dry-run unless env gates live) — **open**.
- `docs/api-contract.md`: sensor column rows — **done** on the branch (rows `ax..gz` … `lfEnergy / usEnergy`, and the
  `features_live.run_live` → `meta/features/<deviceId>/<ts>.json` note).

## Wire fields

All additive under `schemaVersion: 1`; telemetry sensor fields are optional heartbeat keys, features fields
live only in `meta/features/…` (never authoritative).

Telemetry (optional, additive):

| Field | Type | Notes |
|-------|------|-------|
| `ax` `ay` `az` | number (g) | DeviceMotion accel axes |
| `gx` `gy` `gz` | number (rad/s) | DeviceMotion rotation-rate axes |
| `accelAxes` / `gyroAxes` | `[x, y, z]` | 3 floats; synthesised from scalar axes when absent |
| `outLevel` | number (dB) | TX output level estimate |
| `micDiff` | number (dB) | `micEnergy − 0.85·outLevel` (α = 0.85); phone value wins when present |
| `bandBurst` | `lf` \| `us` \| `both` \| absent | LF ≥ −60 dB / US ≥ −55 dB band burst |
| `soundBurst` | bool | Phone-side burst detector |
| `extremeActive` | bool | Phone-side extreme-mode flag |
| `lfEnergy` / `usEnergy` | number (dB) | Band energies |
| `lastHopAgeMs` | int | ms since last hop |
| `ctxResumes` / `watchdogTrips` | int | AudioContext resume / watchdog counters |

Features object (`meta/features/<deviceId>/<ts>.json`, additive over `colab_etl.extract_features`):

| Field | Type | Notes |
|-------|------|-------|
| `sensors` | object | Projected latest sensor columns incl. computed `micDiff`, `bandBurst` |
| `shriekBias` | bool | `soundBurst ∨ extremeActive ∨ micDiff > 6 dB` — hint only, patch author still clamps |
| `sourceCount` | int | Points consumed (≤ `limit`) |
| `live` | bool | `true` only when written to GCS with `LIVE_GCS=1` |
| `sensorColumns` | list[str] | `SENSOR_COLUMNS` |
| `micDiffAlpha` | number | `0.85` |
| `writer` | string | `iot_asp_autoroute.features_live` |

## Clamps / safety

- **Never writes `meta/patches/`**: `assert_not_patch_path` raises `ValueError` before any write; the only
  write target is `meta/features/<node>/<ts>.json`.
- No patch authoring here: `shriekBias` is a feature, not a patch; `clamps.validate_patch` remains the single
  policy source and `tools.write_patch` still refuses on `holdManual`. `holdManual` telemetry is projected
  unchanged (it is in `TELEMETRY_FEATURE_COLUMNS`), so downstream authors can still refuse.
- Secrets by name only: `GCP_SA_JSON`, `IOT_ASP_GCS_BUCKET`, `LIVE_GCS`, `GOOGLE_CLOUD_PROJECT`; values never
  printed, logged, or written into features.
- Live write requires **both** `LIVE_GCS == "1"` and a non-empty `IOT_ASP_GCS_BUCKET`; anything else is the
  dry-run mirror. Tests run with `IOT_ASP_AUTOROUTE_DRY_ROOT=<tmp_path>` and never import
  `google.cloud.storage`.
- Vib series is `absA`/`a` in g at 1 Hz through the shared `vib_anomaly` (no re-implementation).
- Physics honesty: `lfEnergy` is a felt-proxy band energy, not infrasound capture; no CFD claims; `bandBurst`
  thresholds are heuristic labels.
- No PII: sensor columns are device metrics only.

## Acceptance tests (`tests/test_features_live.py`, offline, deterministic)

| ID | Test | Check |
|----|------|-------|
| FL-01 | `mic_diff(-40.0, -30.0)` | `== pytest.approx(-14.5)`; `mic_diff(-40.0, -30.0, given=3.25) == 3.25`; `mic_diff(None, None) == 0.0` |
| FL-02 | `band_burst` | `(-50,-50)→'both'`, `(-50,-70)→'lf'`, `(-70,-50)→'us'`, `(-70,-70)→None`, `(None,None)→None` |
| FL-03 | `project_sensor_features` | axes coerced to 3 floats; `accelAxes` synthesised from `ax,ay,az`; a 2-element `gyroAxes` dropped; `bandBurst='nope'` dropped; unknown key ignored |
| FL-04 | `parse_telemetry_objects` | one `.jsonl` (3 lines, one malformed) + two `.json` → 4 points sorted by `ts` ascending; `latest_points(node, limit=2)` returns the 2 newest; epoch-ms `ts` normalised to ISO |
| FL-05 | `build_feature_record` | with 12 points: `sourceCount == 12`, `anomaly.n == 12`, `sensors.micDiff == pytest.approx(micEnergy − 0.85·outLevel)`, `kind == "iot_asp_features"`, `schemaVersion == 1` |
| FL-06 | `shriekBias` | true for `soundBurst=True`; true for `extremeActive=True`; true for `micDiff=6.5`; false for `micDiff=5.9` with both flags false |
| FL-07 | `run_live` dry-run | `monkeypatch` `gcs_io.DRY_RUN=True`, `gcs_io.DRY_ROOT=tmp_path`, `IOT_ASP_AUTOROUTE_DRY_ROOT=tmp_path`, env `LIVE_GCS` unset: after `_seed_demo` + `run_live("node1", 50)`, exactly one file under `tmp_path/meta/features/node1/`, name ends with `.json` and has no `:`; `not (tmp_path/"meta/patches").exists()`; result `ok is True`, `live is False`, `uri.startswith("file://")`, `sourceCount == 12` |
| FL-08 | Guard | `assert_not_patch_path("meta/patches/node1.json")` raises `ValueError`; `assert_not_patch_path("meta/features/node1/x.json")` does not |
| FL-09 | Env gate | with `LIVE_GCS=1` but `IOT_ASP_GCS_BUCKET` unset, `run_live(..., write=False)["live"] is False`; with both set and `write=False` (reads stubbed via `monkeypatch` on `latest_points`), `live is True`, `gcs_io.DRY_RUN` was `False` during the run and restored after, nothing is written; explicit `live=True` without a bucket → `live is False` |
| FL-10 | No telemetry | `run_live("ghost", write=True)` → `ok is False`, no file created |
| FL-11 | CLI | `python3 -m iot_asp_autoroute.features_live --node node1 --limit 50 --seed-demo` with `IOT_ASP_AUTOROUTE_DRY_ROOT=<tmp>` exits 0 and prints JSON with `"ok": true` and a `file://` uri (subprocess, `PYTHONPATH=services/autoroute-adk`) |
| FL-12 | Notebook sync | `.ipynb` parses as JSON with `nbformat == 4`; code-cell sources concatenated contain `userdata.get("GCP_SA_JSON")`, `userdata.get("IOT_ASP_GCS_BUCKET")`, `userdata.get("LIVE_GCS")`, `features_live.run_live(`, `services/autoroute-adk`; do **not** contain `meta/patches` or key-like patterns; the `.md` file contains the same three names and `run_live(`, its ```python fences equal the `.ipynb` code cells in order, and every `.ipynb` markdown cell appears in the `.md` |
| FL-13 | Constants | `ALL_COLUMNS[:len(TELEMETRY_FEATURE_COLUMNS)] == TELEMETRY_FEATURE_COLUMNS`; `MIC_DIFF_ALPHA == 0.85`; `len(SENSOR_COLUMNS) == 18` |

## CI gate

- `tests` job: `python3 -m pytest tests/test_features_live.py -q` (part of `pytest tests -q`) — offline, `tmp_path` dry root.
- `autoroute` job import smoke may add `from iot_asp_autoroute import features_live` (integration request; not required).
- `bash scripts/ci_static_gates.sh` and `bash scripts/autoroute_dev.sh` remain unchanged and green (module is not on their path).
- Live GCS execution is **not** a CI gate (`docs/ci.md` "Out of scope"); evidence is `.vv/colab-sensors.md`.

## Risks / HW limits

- `gcs_io.list_prefix` dry-run only globs `*.json`; `.jsonl` support lives in `features_live.latest_points`
  (extra glob) rather than a `gcs_io` edit (not owned). Live `list_blobs` returns both.
- `ts` ordering: object names replace `:` with `-`; sort uses the parsed `ts` field, not the name, so mixed
  ISO / epoch-ms inputs order correctly.
- Sensor fields are not yet emitted by `public/index.html` on `origin/main`; until the Mac frontend merges,
  live runs will produce records with an empty `sensors` block except computed `micDiff` when
  `micEnergy`+`outLevel` exist (`micEnergy` is stored "as sent", dB or linear — `micDiff` is only meaningful
  when both are dB).
- iOS DeviceMotion at ~1 Hz beacon rate: gyro/accel axes are coarse; LF energy is a felt proxy, not infrasound.
- Colab service-account JSON is written to a temp file for `GOOGLE_APPLICATION_CREDENTIALS`; the notebook
  must not print it and the runtime is ephemeral.
- `google-cloud-storage` pinned `>=2.14,<4` in `services/autoroute-adk/requirements.txt`; the live path is only
  exercised in Colab, not CI.

## Sources

- Context7 `/jupyter/nbformat` — notebook top-level keys (`cells`, `metadata`, `nbformat: 4`, `nbformat_minor`), markdown/code cell shapes (`cell_type`, `metadata`, `source`, code cells add `execution_count`, `outputs`).
- Context7 `/googleapis/python-storage` (v3.x) — `Client(project=, credentials=)`, `list_blobs(bucket_or_name, prefix=)`, `Blob.upload_from_string(data, content_type=)`.
- Firecrawl developer search — Colab secrets API `from google.colab import userdata; userdata.get('<NAME>')`: https://guides.library.stanford.edu/api_auth/colab , https://github.com/googlecolab/colab-vscode/issues/215
- Repo: `docs/api-contract.md`, `docs/colab-gemini-pipeline.md`, `.claude/rules/autoroute-backend.md`, `.claude/rules/docs-and-specs.md`, GitHub issue #26.
