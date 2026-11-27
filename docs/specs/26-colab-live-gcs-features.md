# #26 — Colab live GCS: accel / gyro / micDiff telemetry → `meta/features`

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/26 (parent #17, milestone M3)
Owned files: `services/autoroute-adk/iot_asp_autoroute/features_live.py`, `tests/test_features_live.py`,
`notebooks/iot_asp_colab_etl.md`, `notebooks/iot_asp_colab_etl.ipynb`, `.vv/colab-sensors.md`, this spec.

## Status

**Done on main (dry-run / offline path).** Closeout evidence: `.vv/26/colab-gcs-closeout.md` (2026-10-12).
`features_live.py`, `tests/test_features_live.py` (FL-01 … FL-16), notebooks, `.vv/colab-sensors.md`,
and the hermetic fixture scripts are on `main`. Offline path is CI-tested.
Live GCS write remains **owner-gated** (`LIVE_GCS=1` + Colab `userdata` names `GCP_SA_JSON`,
`IOT_ASP_GCS_BUCKET`); recorded as `live: PENDING` in `.vv/colab-sensors.md`. No secret values in git.

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
| **Review fix (2026-09-08):** object names are built only from validated parts — `validate_node` (`^[A-Za-z0-9_-]+$`), `features_object_name` requires a strict ISO-8601 `ts` (`TS_RE`), `assert_not_patch_path` also refuses absolute names and `""`/`.`/`..` segments, and `assert_features_path` resolves the dry-run target under `DRY_ROOT/meta/features/`. `normalize_ts` returns `None` (never the raw string) for unparseable input; `.jsonl` lines without a usable `ts` are dropped and reported as `unparseable ts` instead of being string-sorted last. `run_live` / `_seed_demo` / `list_telemetry_names` raise `ValueError` on a bad node before any I/O; the CLI maps that to `{"ok": false, "error": …}` exit 2 | `features_live.py`; FL-14 … FL-16 |

## Goal

Extend (never modify) the shared Colab/ADK ETL so that telemetry heartbeats carrying phone
**accelerometer / gyroscope / mic-spectrum** sensor fields (`ax..gz`, `accelAxes`, `gyroAxes`,
`outLevel`, `micDiff`, `bandBurst`, `soundBurst`, `extremeActive`, `lfEnergy`, `usEnergy`, …) are
projected into a **features** object under `meta/features/<deviceId>/<ts>.json`, computed from the last
`limit` telemetry points (objects or JSONL), with a `shriekBias` hint for the patch author. The module is
runnable offline (`--seed-demo`) and from Colab with secrets referenced **by name only**. It never writes
`meta/patches/` (Colab/ETL is never authoritative — CLAUDE.md "Storage" cheat-sheet and
`.claude/rules/autoroute-backend.md`).

## Prior art

Checked 2026-09-08 (UTC), in the order CLAUDE.md prescribes; register row in `docs/PRIOR_ART.md`
("`iot_asp_autoroute/features_live.py` → Extend, do not duplicate").

- **This repo (`rg`, `git log -S`, `origin/*`):** `colab_etl.extract_features` / `normalize_telemetry` /
  `TELEMETRY_FEATURE_COLUMNS` (offline feature record), `vib_anomaly.detect_disturbances` (the authoritative
  SciPy detector — `.claude/rules/autoroute-backend.md` forbids re-implementing it in notebooks), `gcs_io`
  (dry-run mirror + GCS adapter), `tools.read_telemetry` (lexicographic `names[-1]`, no `.jsonl`, no ts
  parsing), `fleet_log` (#22, writes daily `.jsonl` under `meta/logs/`), the notebook stub cells
  `latest_telemetry` / `vib_features` (sketch only). Nothing read `.jsonl` telemetry, projected the sensor
  columns, or wrote `meta/features/` with a patch-path guard. **Decision: extend** — import `colab_etl`,
  `vib_anomaly`, `gcs_io`; add only the live read path, sensor projection, and the write guard.
- **Owner's Mac clone (per issues #25/#26):** the frontend already emits `micDiff = micEnergy − 0.85·outLevel`,
  `bandBurst`, `soundBurst`, `extremeActive`; not on `origin`. The backend therefore treats those as additive
  optional keys and never recomputes a phone-supplied `micDiff` (α = 0.85 kept identical).
- **Org repos:** not reachable from this session (no network to the org); nothing in `docs/PRIOR_ART.md` or the
  issue thread names another implementation. Re-check before extending if `timestore.py` lands (#20).
- **Awesome-lists / OSS:** `pandas.read_json(..., lines=True)` over `gs://` via `gcsfs` (Firecrawl:
  https://clickhouse.com/resources/engineering/read-jsonl-file-python ,
  https://markusodenthal.medium.com/the-easy-way-to-read-files-from-google-cloud-storage-with-pandas-or-dask-3a424b71af14)
  and chDB `DataStore.read_json` (Firecrawl: https://github.com/clickhouse/clickhouse-docs — chdb/datastore
  factory methods) would read JSONL from GCS, but each adds a dependency (`pandas`/`gcsfs`/`chdb`) to a
  stdlib-first ADK package for ≤ 200 heartbeats per run and gives no per-line error reporting or ts
  normalisation. **Decision: build the ~40-line reader on `gcs_io`** (`google-cloud-storage` is already
  pinned; Context7 `/googleapis/python-storage`).
- **Object-name safety (review finding):** the same bug class — joining a storage object name containing
  `..` onto a local directory — was fixed in Apache Airflow's Google provider by resolving the joined path and
  refusing when it leaves the destination (Firecrawl: https://github.com/apache/airflow/issues/67667). GCS
  itself is a flat namespace (https://docs.cloud.google.com/storage/docs/hns-overview) and object-store naming
  guidance warns that `.`/`..` segments are interpreted as relative references by tools
  (https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-keys.html), so the live bucket is not the
  exposure — the dry-run mirror is. **Adopted:** validate inputs (`validate_node`, `TS_RE`) *and* resolve the
  target under `DRY_ROOT/meta/features/` (`assert_features_path`), as Airflow did.

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
| `normalize_ts(ts) -> str \| None` | ISO-8601 `%Y-%m-%dT%H:%M:%SZ` from ISO strings (any offset → UTC), epoch s / ms, or the object-name form `…T00-00-05Z`. **Returns `None` for anything unparseable — never the raw input.** |
| `validate_node(node) -> str` | `str(node)` iff it matches `^[A-Za-z0-9_-]+$`; else `ValueError("refuse: node id …")`. Called by `list_telemetry_names`, `features_object_name`, `run_live`, `_seed_demo` before any I/O. |
| `parse_telemetry_objects(names, reader=gcs_io.read_json, text_reader=None, errors=None) -> list[dict]` | Accepts object names under `meta/telemetry/<node>/`. `*.json` → one point; `*.jsonl` → one point per non-blank line (bad lines skipped, appended to `errors` as `{object, line, error}`). Every point is `colab_etl.normalize_telemetry`'d; `ts` may be ISO-8601 or epoch ms (ms → `%Y-%m-%dT%H:%M:%SZ`). A `*.json` object without a usable `ts` falls back to its name stem (ingest names objects by ts); a `*.jsonl` line without a usable `ts` is **dropped** with `error: "unparseable ts"` (never string-sorted). Result sorted by `ts` ascending, stable on name then line. |
| `latest_points(node, limit=200) -> list[dict]` | `gcs_io.list_prefix(f"meta/telemetry/{node}/")` **plus** `.jsonl` siblings (dry-run: extra `rglob("*.jsonl")` under `DRY_ROOT`; live: names already come from `list_blobs`) → `parse_telemetry_objects` → keep the last `limit`. |
| `build_feature_record(points, node) -> dict` | Requires `points` non-empty (else `ValueError`). `latest = points[-1]`; `vib_series = [absA or a]` over all points (1 Hz, `SAMPLE_HZ`), skipping points without either key. Calls `colab_etl.extract_features(latest, vib_series=vib_series)` and **adds** additive keys: `sensors` (projected latest sensors; `micDiff` computed via `mic_diff(micEnergy, outLevel)` when absent and `micEnergy`+`outLevel` present; `bandBurst` computed via `band_burst(lfEnergy, usEnergy)` when absent), `shriekBias` (bool: `soundBurst is True or extremeActive is True or micDiff > 6.0`), `sourceCount = len(points)`, `live` (bool set by caller, default `False`), `sensorColumns = list(SENSOR_COLUMNS)`, `micDiffAlpha = 0.85`, `writer = "iot_asp_autoroute.features_live"`. `kind` stays `"iot_asp_features"`; `schemaVersion` stays `1`. |
| `features_object_name(node, ts) -> str` | `f"meta/features/{validate_node(node)}/{iso.replace(':', '-')}.json"` where `iso = normalize_ts(ts)` must match `TS_RE` (`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`); otherwise `ValueError`. The name is built from validated parts only — a telemetry-controlled `ts` cannot inject `/` or `..`. |
| `assert_not_patch_path(object_name)` | `ValueError` if the name is absolute, contains `\`, or has any `""` / `.` / `..` segment (`refuse: unsafe object name …`), or if it starts with `meta/patches` (`refuse: features_live never writes meta/patches`). |
| `assert_features_path(object_name)` | `assert_not_patch_path` + must start with `meta/features/` + in dry-run `(DRY_ROOT / name).resolve()` must be under `(DRY_ROOT / "meta/features/").resolve()` (symlink-safe). Called by `run_live` before every write. |
| `run_live(node, limit=200, write=True, live=None) -> dict` | `live` defaults to `os.environ.get("LIVE_GCS") == "1" and bool(os.environ.get("IOT_ASP_GCS_BUCKET"))`. When `live` is `False` the write is forced to the dry-run mirror (`gcs_io.DRY_RUN = True` for the duration; restored after). `node` goes through `validate_node` first (`ValueError` before any read). Reads `latest_points`, builds the record with `record["live"] = live`, computes `name = features_object_name(node, record["ts"])`, `assert_features_path(name)`, writes via `gcs_io.write_json` iff `write`. Returns `{ "ok": bool, "uri": str \| None, "node", "live", "sourceCount", "featureKeys": sorted(record.keys()), "object": name }`; when no telemetry: `{"ok": False, "error": "no telemetry under meta/telemetry/<node>/", ...}` and no write. |
| `_seed_demo(node, n=12, seed=26) -> list[str]` | Writes `n` synthetic points `meta/telemetry/<node>/2026-09-08T00-00-<ss>Z.json` (1 s apart, fixed base ts) to the dry-run mirror via `gcs_io.write_json`: `ax..gz` from `random.Random(seed)`, `absA` from `vib_anomaly.synthetic_demo_series(n, seed)`, `outLevel=-30.0`, `micEnergy=-40.0`, `lfEnergy=-70.0`, `usEnergy=-50.0`, `algo="hop"`, `suddenFreq=False`, `holdManual=False`; point index 9 has `soundBurst=True`, `micEnergy=-20.0`. Returns written URIs. |
| CLI `python3 -m iot_asp_autoroute.features_live --node node1 --limit 50 [--live] [--seed-demo]` | `--seed-demo` runs `_seed_demo` first; without `--live` the run is dry-run regardless of env. Prints one JSON line (the `run_live` result) and exits 0 on `ok`, 2 otherwise. A refused node / ts / path (`ValueError`) prints `{"ok": false, "error": "refuse: …"}` and exits 2 with nothing written. Never prints env values. |

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
| `gx` `gy` `gz` | number (rad/s) | DeviceMotion gyro axes |
| `accelAxes` `gyroAxes` | [number, number, number] | synthesised if scalars present |
| `outLevel` | number (dB) | current output level |
| `micDiff` | number (dB) | micEnergy - 0.85 * outLevel (phone or computed) |
| `bandBurst` | "lf" \| "us" \| "both" \| null | heuristic band label |
| `soundBurst` `extremeActive` | bool | frontend burst flags |
| `lfEnergy` `usEnergy` | number (dB) | felt-proxy / ultrasonic band energy |
| `lastHopAgeMs` `ctxResumes` `watchdogTrips` | int | counters |

Features object (written only to `meta/features/`):

Adds `sensors`, `shriekBias`, `sourceCount`, `live`, `sensorColumns`, `micDiffAlpha`, `sampleHz`, `sourceObjects`, `writer` to the `colab_etl.extract_features` record. `kind` remains `iot_asp_features`. `schemaVersion` remains 1.

## Acceptance

- [x] Offline `--seed-demo` produces `file://` features under `meta/features/` and never `meta/patches/`
- [x] Path safety: bad node / bad ts / `..` refused before write
- [x] Tests FL-01 … FL-16 green
- [ ] Live GCS write with owner `userdata` names (residual)
