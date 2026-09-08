# #22 — Structured fleet telemetry logs (awesome-inspired)

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/22 · Milestone: M6 · Branch: `claude/mdc-conversion-features-gu3yzk`

## Status

**Spec — not yet implemented.** Module `services/autoroute-adk/iot_asp_autoroute/fleet_log.py`,
tests `tests/test_fleet_log.py`, and the integration hooks in `tools.py` do not exist on this checkout.
The issue body says "Partial: beacon + api-contract fields shipped in public HTML"; on this checkout
(`origin/main` @ `0625e91`) the beacon does **not** yet emit `band`/`power`/`nightNY`/`lfArmed`/
`lfDriveCapable` (see *Shipped on main*). The owner's Mac clone may be ahead; this spec treats those
telemetry keys as **optional inputs** and always derives them server-side, so it is correct either way.

## Goal

Every telemetry heartbeat and every autoroute decision produces one **structured, PII-scrubbed,
fixed-shape JSON Lines record** under `meta/logs/<node>/<YYYY-MM-DD>.jsonl`, enriched with the tags
the fleet cares about (`band`, `power`, `nightNY`, `lfArmed`, `lfDriveCapable`, `lfGate`), plus a
deterministic aggregator (`aggregate_records`) and a documented retention/aggregation plan that hands
raw logs and aggregates to the Colab ETL (#17, #26) without ever touching `meta/patches/`.

"Awesome-inspired" = the observability conventions from the curated index (`docs/awesome-iot-asp.md`):
one record per event, fixed key order, `kind` + `schemaVersion` discriminators, level enum, no free-form
PII, date-partitioned JSONL, and a separate aggregate layer with explicit retention.

## Shipped on `main`

Verified by reading the files on this checkout (line numbers are exact):

| What | Where |
|------|-------|
| Storage path `meta/logs/<deviceId>/<date>.jsonl` is already the declared home for logs | `CLAUDE.md:82`; `.claude/rules/autoroute-backend.md:13` ("Colab/ETL code writes `meta/features/` and `meta/logs/` — never `meta/patches/`") |
| Telemetry feature columns already list `band`, `lfDriveCapable`, `lfArmed`, `power`, `nightNY` | `services/autoroute-adk/iot_asp_autoroute/colab_etl.py:47-51` |
| Offline fixture already carries `band: "17-23k"`, `lfDriveCapable: False`, `lfArmed: False`, `power: "ac120"`, `nightNY: False` | `services/autoroute-adk/iot_asp_autoroute/colab_etl.py:229-233` |
| Band inference from tag or `fMin <= 100` (reused, not re-implemented) | `services/autoroute-adk/iot_asp_autoroute/clamps.py:30-43` (`band_limits`), constants `BAND_US`/`BAND_LF` at `clamps.py:12-13` |
| LF drive capability semantics (`lfDriveCapable` / `lfArmed` + band) | `services/autoroute-adk/iot_asp_autoroute/priors.py:203-216` (`lf_drive_capable`) |
| `vibClass` normalisation to `none \| physical \| acoustic \| infra_felt` | `services/autoroute-adk/iot_asp_autoroute/priors.py:151-155`; `colab_etl.py:60` |
| Dry-run storage mirror + env knobs `IOT_ASP_AUTOROUTE_DRY_RUN`, `IOT_ASP_AUTOROUTE_DRY_ROOT` | `services/autoroute-adk/iot_asp_autoroute/gcs_io.py:10-28` (`DRY_ROOT`, `is_dry_run`, `_local_path`) |
| `gcs_io.write_json` serialises with `sort_keys=True` — cannot be used for fixed-order JSONL | `services/autoroute-adk/iot_asp_autoroute/gcs_io.py:31-42` |
| `gcs_io.list_prefix` only globs `*.json` in dry-run — `.jsonl` needs its own listing | `services/autoroute-adk/iot_asp_autoroute/gcs_io.py:60-73` |
| Ingest entry point that will call the enrich + log hook | `services/autoroute-adk/iot_asp_autoroute/tools.py:124-154` (`ingest_telemetry`), ts normalisation at `tools.py:145-150` |
| Decision point that will emit a log record (hold refuse / skipped / authored) | `services/autoroute-adk/iot_asp_autoroute/tools.py:157-175` (`process_sudden_freq`) |
| `is_sudden_freq_event` (used for `suddenFreq` in records) | `services/autoroute-adk/iot_asp_autoroute/sudden_freq.py:42-53` |
| Phone beacon payload — device metrics only, **no** `band`/`power`/`nightNY`/`lf*` yet | `public/index.html:1332-1360` (`telemetryPayload`), `sendBeacon` at `:1367-1368` |
| API contract telemetry table lacks rows for the five enrichment fields | `docs/api-contract.md:64-79` |

## Remaining scope

1. **`fleet_log.py`** (stdlib only; `zoneinfo` for `America/New_York`):
   - `NY_TZ = zoneinfo.ZoneInfo("America/New_York")`; `NIGHT_HOURS = range(22, 24) ∪ range(0, 7)`.
   - `parse_ts(ts) -> datetime | None`: accepts ISO-8601 with `Z` or offset (`datetime.fromisoformat`
     after replacing a trailing `Z` with `+00:00`; 3.11 parses most ISO-8601 forms), the filename form
     `%Y-%m-%dT%H-%M-%SZ` (as written by `tools.py:145-150`), epoch **ms** (`> 1e12`) or epoch **s**
     (numeric). Naive strings are treated as UTC. Anything else → `None`.
   - `to_wire_ts(dt) -> str`: `%Y-%m-%dT%H:%M:%SZ` in UTC.
   - `night_ny(ts) -> bool`: `parse_ts(ts)` → `astimezone(NY_TZ)` → hour ∈ `[22,24) ∪ [0,7)`;
     `None`/unparseable → `False`.
   - `infer_band(t) -> "17-23k" | "10-20"`: `clamps.band_limits(t) == clamps.BAND_LF` → `"10-20"`
     else `"17-23k"` (this already covers "band says so" *and* `fMin <= 100`).
   - `scrub_pii(obj) -> tuple[dict, list[str]]`: recursive over dicts (lists of dicts included).
     A key is **dropped** when its lowercase form is in `PII_DENY_EXACT`
     (`recordinguri`, `recording_uri`, `latitude`, `longitude`) **or** any token of the key
     (split on `_`, `-`, and camelCase boundaries, lowercased) is in `PII_DENY_TOKENS` =
     `{address, street, name, email, phone, lat, lon, gps, ip, transcript, speech, recording}`.
     Returns `(clean_copy, sorted_dropped_key_names)`. The dropped **values are never returned,
     logged, or placed in `msg`** — only key names and a count. Contract keys (`deviceId`, `schemaVersion`,
     `micEnergy`, `vibThreshold`, `pulseMs`, `shriekMs`, `lfDriveCapable`, `suddenFreqMeta`, …)
     contain none of the deny tokens and must survive (test asserts this against
     `colab_etl.TELEMETRY_FEATURE_COLUMNS`).
   - `enrich_telemetry(t) -> dict`: pure; never mutates input. Steps: `scrub_pii` → copy → set
     `band = infer_band(t)` (only if absent or not in `{"17-23k","10-20"}`; a valid explicit tag wins),
     `power = t.get("power") or "ac120"`, `nightNY = night_ny(t.get("ts"))` (always recomputed from
     `ts`; a phone-supplied `nightNY` is advisory only), `lfArmed = bool(t.get("lfArmed", False))`,
     `lfDriveCapable = bool(t.get("lfDriveCapable", False))`,
     `vibClass = priors.normalize_vib_class(t.get("vibClass"))`,
     `lfGate = lfArmed and lfDriveCapable and vibClass == "infra_felt"`,
     `piiDropped = <count>` (int, only when > 0). Idempotent: `enrich(enrich(t)) == enrich(t)`.
     `lfGate` is a **log tag**, not a clamp decision; `clamps.validate_patch` and
     `priors.lf_drive_capable` stay authoritative for patches.
   - `log_record(level, event, telemetry, msg="", *, now=None) -> dict` with **fixed key order**
     (`RECORD_KEYS`, 21 keys):
     `kind="fleet_log"`, `schemaVersion=1` (imported from `clamps.SCHEMA_VERSION`), `ts`, `level`,
     `event`, `deviceId`, `band`, `power`, `nightNY`, `lfArmed`, `lfDriveCapable`, `lfGate`, `algo`,
     `vibClass`, `suddenFreq`, `suddenState`, `holdManual`, `peakHz`, `absA`, `micEnergy`, `msg`.
     `level` ∈ `{"debug","info","warn","error"}` else `ValueError`. `ts` = `to_wire_ts(parse_ts(t["ts"]))`
     when parseable, else `to_wire_ts(now or datetime.now(timezone.utc))`. `deviceId` = `deviceId` or
     `nodeId` or `"node1"`. `algo` = `sudden_freq.normalize_algo(...)`. `suddenFreq` =
     `sudden_freq.is_sudden_freq_event(enriched)`. `absA` falls back to `a`. Missing numerics → `None`.
     `msg` is passed through **after** truncation to 240 chars and must not contain dropped PII values
     (callers only ever pass key names/counts). `list(record) == RECORD_KEYS` always.
   - `record_path(node, ts) -> str`: `meta/logs/<node>/<YYYY-MM-DD>.jsonl`, date = **UTC** date of the
     record `ts`. `node` is sanitised to `[A-Za-z0-9_.-]` (anything else → `_`).
   - `write_log_record(node, record) -> dict {ok, uri, path, mode}`:
     - **dry-run** (`gcs_io.is_dry_run()`): resolve root = `os.environ.get("IOT_ASP_AUTOROUTE_DRY_ROOT")`
       if set **at call time**, else `gcs_io.DRY_ROOT`; `mkdir -p`; open in `"a"` mode, UTF-8, write
       `json.dumps(record, ensure_ascii=False, separators=(",", ":"))` + `"\n"` (no `sort_keys`).
       `uri = "file://<path>"`, `mode = "append"`.
     - **live GCS** (`google.cloud.storage`, deferred import, ADC only): Cloud Storage objects are
       immutable and there is no append, so the writer does **read-modify-write**:
       `blob.reload()` → `download_as_text()` (or `""` when the blob does not exist, generation `0`) →
       concatenate the new line → `upload_from_string(body, content_type="application/x-ndjson",
       if_generation_match=<generation seen>)`. A `412 Precondition Failed` is retried up to 3 times
       (re-read then re-upload); after that the record is written as a side-file
       `meta/logs/<node>/<YYYY-MM-DD>.<ts-safe>.part.jsonl` so no record is lost, and `mode =
       "rmw-fallback"`. Normal path `mode = "rmw"`. The writer never uses `gcs_io.write_json`
       (its `sort_keys=True` would destroy key order).
   - `read_log_records(node, date=None) -> list[dict]`: `date` = `YYYY-MM-DD` string or `None` = all
     dates for the node, ascending by filename then line. Parses one JSON object per non-blank line;
     malformed lines are skipped and counted (returned via a `_skipped` attribute on the list is
     **not** allowed — return the list only; expose `read_log_records_with_stats` if a count is needed).
     Dry-run lists `*.jsonl` (incl. `.part.jsonl`) under the node dir itself; live lists
     `client.list_blobs(BUCKET, prefix=f"meta/logs/{node}/")` filtered to `.jsonl`.
   - `aggregate_records(records, window_s=300, node=None) -> dict` with keys in this order:
     `node` (arg, else first record's `deviceId`, else `None`), `first_ts`, `last_ts` (wire strings,
     min/max of record `ts`; `None` on empty), `count`, `sudden_count` (records with `suddenFreq is
     True`), `hold_fraction` (`holdManual` true ÷ count, `round(…, 4)`, `0.0` on empty),
     `night_fraction` (same for `nightNY`), `by_algo`, `by_vibClass`, `by_band`, `by_level`
     (dicts with **sorted** keys → int counts; missing values bucket as `"unknown"`), `windows`:
     list of `{start, end, count, sudden}` for **non-empty** windows only, aligned to epoch multiples
     of `window_s` (`floor(epoch / window_s) * window_s`), ascending, `end = start + window_s`, both
     wire strings. `window_s <= 0` → `ValueError`. Pure function; input order irrelevant.
   - `retention_plan() -> dict` (see *Retention / aggregation* below); pure constant data.
   - CLI: `python3 -m iot_asp_autoroute.fleet_log --demo` → sets `IOT_ASP_AUTOROUTE_DRY_RUN=1` if
     unset, builds the 12-record fixture (`demo_fixture()`), prints one enriched sample record and the
     aggregate as JSON, exits 0. `--demo` must not require network, numpy, scipy, or `google-adk`.
     Running without args prints usage and exits 2.
2. **`tests/test_fleet_log.py`** — see *Acceptance tests*.
3. **Integration (integrator-owned files, requested not edited here):**
   - `tools.py::ingest_telemetry`: `tel = fleet_log.enrich_telemetry(tel)` **before** `gcs_io.write_json`,
     then `fleet_log.write_log_record(node, fleet_log.log_record("info", "ingest", tel))`.
   - `tools.py::process_sudden_freq`: emit `warn`/`hold_refuse` when `holdManual`, `debug`/`skipped`
     when not an event, `info`/`patch_authored` (msg = clamp message) or `error`/`patch_refused` (msg =
     error text) after `write_patch`.
   - New ADK tool `tools.fleet_log_summary(node_id: str, date: str | None = None) -> dict` →
     `aggregate_records(read_log_records(node_id, date or <today UTC>), node=node_id)` wrapped as
     `{"ok": True, "date": ..., "summary": ...}`; empty → `{"ok": True, "summary": {count: 0 ...}}`.
   - `docs/api-contract.md`: add five optional telemetry rows (below).
   - `ingest_main.py`: no change expected (calls `ingest_telemetry`).

## Wire fields

All **additive** under `schemaVersion: 1`; no bump. Telemetry keys are optional on the wire and always
normalised server-side by `enrich_telemetry`.

Telemetry (rows to add to `docs/api-contract.md` telemetry table):

| Field | ★ | Type | Notes |
|-------|---|------|--------|
| `band` | | string | `17-23k` (default) \| `10-20`; inferred from tag or `fMin <= 100` when absent |
| `power` | | string | Default `ac120` (fleet is continuous 120 V AC, C5); free-form tag, no clamp effect |
| `nightNY` | | bool | Server recomputes from `ts` in `America/New_York`: hour ∈ [22,24) ∪ [0,7); phone value advisory |
| `lfArmed` | | bool | Operator armed LF 10–20 Hz TX; default `false` |
| `lfDriveCapable` | | bool | Hardware can drive 10–20 Hz; default `false`; required with `lfArmed` + `vibClass=infra_felt` for `lfGate` |

Log record (`meta/logs/<node>/<YYYY-MM-DD>.jsonl`, one object per line, fixed order):

```json
{"kind":"fleet_log","schemaVersion":1,"ts":"2026-01-15T11:55:00Z","level":"info","event":"ingest","deviceId":"node1","band":"17-23k","power":"ac120","nightNY":true,"lfArmed":false,"lfDriveCapable":false,"lfGate":false,"algo":"hop","vibClass":"none","suddenFreq":false,"suddenState":"idle","holdManual":false,"peakHz":19500,"absA":0.12,"micEnergy":0.03,"msg":""}
```

`event` values emitted by the backend: `ingest`, `hold_refuse`, `skipped`, `patch_authored`,
`patch_refused`. Consumers must ignore unknown `event` values and unknown trailing keys.

Aggregate object (`aggregate_records`, also what `fleet_log_summary` returns under `summary`):
`{node, first_ts, last_ts, count, sudden_count, hold_fraction, night_fraction, by_algo, by_vibClass,
by_band, by_level, windows:[{start,end,count,sudden}]}`.

## Clamps / safety

- **No clamp changes.** `fleet_log` imports `clamps.band_limits`, `clamps.SCHEMA_VERSION`,
  `priors.normalize_vib_class`, `sudden_freq.normalize_algo`, `sudden_freq.is_sudden_freq_event`; it
  never calls `validate_patch` and never writes `meta/patches/` or `meta/telemetry/`.
- `vol_hard_max == vol_soft_max == 100.0` untouched; `ALLOWED_ALGOS`, `BAND_US`, `BAND_LF` untouched.
- **Hold / Manual wins:** logging a `hold_refuse` record is observability only; the refuse path in
  `tools.py:167-168` / `write_patch` (`tools.py:62-67`) is unchanged and runs before any log write.
  A log write failure must never turn a refuse into an authored patch (log calls are wrapped so
  exceptions are returned as `{ok: False, error}` and do not propagate into the decision path).
- `lfGate` requires **all three** of `lfArmed`, `lfDriveCapable`, `vibClass == "infra_felt"`; it mirrors
  the LF band policy in `priors.band_for_telemetry` (`priors.py:237-267`) but has no authority.
- **PII:** `scrub_pii` runs before anything is written or aggregated. Records never include free-text
  from the phone other than `msg` authored by the backend. Dropped values are discarded in memory and
  never echoed (the test patches `json.dumps` inputs to assert absence of a sentinel value).
- **Secrets by name only:** `GOOGLE_CLOUD_PROJECT`, `IOT_ASP_GCS_BUCKET`, `GCP_SA_JSON` (Colab). The
  module never prints env values.
- **Physics honesty:** records carry `vibClass=infra_felt` as the felt proxy label; nothing in this
  module claims infrasound capture or CFD.
- Unknown `vibClass` → `none`; unknown `algo` alias → passed through `normalize_algo` (UI aliases mapped,
  otherwise the string is kept — the aggregate buckets it verbatim, the clamp layer still refuses it).

## Acceptance tests

`tests/test_fleet_log.py` — offline, deterministic, no numpy/scipy import, `tmp_path` +
`monkeypatch.setenv("IOT_ASP_AUTOROUTE_DRY_ROOT", str(tmp_path))` + `monkeypatch.setenv
("IOT_ASP_AUTOROUTE_DRY_RUN", "1")`. Run: `python3 -m pytest tests/test_fleet_log.py -q`.

1. **enrich determinism / purity:** `enrich_telemetry(t)` called twice on the same dict returns equal
   dicts; input dict is unchanged (`copy.deepcopy` compare); `enrich(enrich(t)) == enrich(t)`.
2. **nightNY boundaries — EST (2026-01-15, UTC−5):**
   `night_ny("2026-01-16T02:59:59Z") is False` (NY 21:59:59),
   `night_ny("2026-01-16T03:00:00Z") is True` (NY 22:00:00),
   `night_ny("2026-01-15T11:59:59Z") is True` (NY 06:59:59),
   `night_ny("2026-01-15T12:00:00Z") is False` (NY 07:00:00).
3. **nightNY boundaries — EDT (2026-07-15, UTC−4):**
   `night_ny("2026-07-16T01:59:59Z") is False`, `night_ny("2026-07-16T02:00:00Z") is True`,
   `night_ny("2026-07-15T10:59:59Z") is True`, `night_ny("2026-07-15T11:00:00Z") is False`.
4. **ts forms:** epoch ms `1768478400000` (= `2026-01-15T12:00:00Z`) → `False`; epoch ms
   `1768478399000` → `True`; missing `ts` → `False`; `"garbage"` → `False`; filename form
   `"2026-01-15T11-59-59Z"` → `True`.
5. **band inference:** `{}` → `17-23k`; `{"band": "10-20"}` → `10-20`; `{"band": "lf"}` → `10-20`;
   `{"fMin": 15}` → `10-20`; `{"fMin": 17000}` → `17-23k`; `{"band": "bogus", "fMin": 17000}` →
   `17-23k`; `{"band": "17-23k", "fMin": 15}` → `17-23k` (explicit valid tag wins).
6. **defaults:** enriched record of `{"deviceId": "node1", "ts": "2026-01-15T12:00:00Z"}` has
   `power == "ac120"`, `lfArmed is False`, `lfDriveCapable is False`, `lfGate is False`,
   `vibClass == "none"`. `power: "battery"` is preserved verbatim.
7. **lfGate truth table:** exactly the combination `lfArmed=True, lfDriveCapable=True,
   vibClass="infra_felt"` gives `True`; the other 7 combinations (including `vibClass="physical"`) give
   `False`. Bool coercion: `lfArmed: 1` → `True`, `lfArmed: "yes"` → `True`, `None` → `False`.
8. **PII scrub:** input with keys `streetAddress`, `name`, `contactEmail`, `phone`, `lat`, `lon`,
   `gpsFix`, `clientIp`, `transcript`, `speechText`, `recordingUri`, `latitude`, nested
   `{"meta": {"homeAddress": "SENTINEL"}}`, all values `"SENTINEL_PII"` → none of those keys exist in
   the output (nested included), `piiDropped == 13`, every key of
   `colab_etl.sample_telemetry_fixture()` survives unchanged, and
   `"SENTINEL_PII" not in json.dumps(enriched)` **and** `"SENTINEL_PII" not in json.dumps(log_record(
   "info", "ingest", enriched, msg=f"dropped={dropped}"))`.
9. **record key order:** `list(log_record("info","ingest",t).keys()) == fleet_log.RECORD_KEYS` and
   `RECORD_KEYS == ["kind","schemaVersion","ts","level","event","deviceId","band","power","nightNY",
   "lfArmed","lfDriveCapable","lfGate","algo","vibClass","suddenFreq","suddenState","holdManual",
   "peakHz","absA","micEnergy","msg"]`; `record["kind"] == "fleet_log"`, `record["schemaVersion"] ==
   1`; `log_record("fatal", ...)` raises `ValueError`; a 1000-char `msg` is truncated to 240.
10. **JSONL round-trip (dry-run, tmp_path):** write the 12-record fixture with `write_log_record`;
    file `tmp_path/meta/logs/node1/2026-01-15.jsonl` exists with exactly 12 lines, each
    `json.loads`-able, first line's key order equals `RECORD_KEYS` (check via
    `list(json.loads(line, object_pairs_hook=OrderedDict))`); `read_log_records("node1",
    "2026-01-15") == fixture_records`; `read_log_records("node1")` returns the same 12;
    `read_log_records("node9") == []`; a hand-appended malformed line `"{not json"` is skipped and
    the count stays 12; returned `uri` starts with `file://` and `mode == "append"`; nothing is created
    under the repo `.autoroute-dry/`.
11. **aggregate math (12-record fixture, `demo_fixture()`):** node `node1`, ts `2026-01-15T11:55:00Z
    + i·60 s` for `i = 0..11`; `suddenFreq=True` for `i ∈ {1,4,7}`; `holdManual=True` for
    `i ∈ {6,7,8}` with `level="warn"`, else `level="info"`; `algo` cycles `hop, am_gate, burst`;
    `vibClass` = `["none","physical","acoustic","infra_felt"][i % 4]`; `fMin=15` for `i ∈ {10,11}`
    else `17000`. Expected `aggregate_records(records, window_s=300)`:
    `count == 12`, `first_ts == "2026-01-15T11:55:00Z"`, `last_ts == "2026-01-15T12:06:00Z"`,
    `sudden_count == 3`, `hold_fraction == 0.25`, `night_fraction == round(5/12, 4) == 0.4167`,
    `by_algo == {"am_gate": 4, "burst": 4, "hop": 4}`,
    `by_vibClass == {"acoustic": 3, "infra_felt": 3, "none": 3, "physical": 3}`,
    `by_band == {"10-20": 2, "17-23k": 10}`, `by_level == {"info": 9, "warn": 3}`,
    `windows == [{"start":"2026-01-15T11:55:00Z","end":"2026-01-15T12:00:00Z","count":5,"sudden":2},
    {"start":"2026-01-15T12:00:00Z","end":"2026-01-15T12:05:00Z","count":5,"sudden":1},
    {"start":"2026-01-15T12:05:00Z","end":"2026-01-15T12:10:00Z","count":2,"sudden":0}]`.
    Shuffling the input (seeded `random.Random(42)`) yields an identical aggregate.
    `aggregate_records([])` → `count 0`, fractions `0.0`, `first_ts is None`, `windows == []`.
    `aggregate_records(records, window_s=0)` raises `ValueError`.
12. **retention_plan():** `plan["raw"]["prefix"] == "meta/logs/"`, `plan["raw"]["days"] == 30`,
    `plan["aggregates"]["prefix"] == "meta/logs-agg/"`, `plan["aggregates"]["days"] == 365`,
    `plan["features"]["prefix"] == "meta/features/"`, `"meta/patches/" not in json.dumps(plan)
    .replace("never meta/patches/", "")` (i.e. patches only appear in the prohibition sentence),
    `plan["lifecycle"]["rule"]` is a list of two `Delete` rules with `condition.matchesPrefix` and
    `condition.age` matching the above.
13. **CLI demo:** `subprocess.run([sys.executable, "-m", "iot_asp_autoroute.fleet_log", "--demo"],
    cwd="services/autoroute-adk", env={..., "IOT_ASP_AUTOROUTE_DRY_ROOT": tmp_path})` exits 0,
    stdout parses as JSON containing `"sample"` (a record with `kind == "fleet_log"`) and
    `"aggregate"` with `count == 12`; stdout contains no key from the PII deny list.
14. **import hygiene:** `sys.modules` after `import iot_asp_autoroute.fleet_log` contains neither
    `numpy` nor `scipy` nor `google.cloud.storage` (test runs in a fresh subprocess).
15. **Negative controls:** `enrich_telemetry({"holdManual": True, ...})` keeps `holdManual is True`
    (never rewritten); nonsense keys (`"__proto__"`, `"priors": ["bogus"]`) pass through unchanged
    (not PII, not our business); `log_record` with `level="INFO"` (uppercase) is normalised to `"info"`.

## CI gate

- `tests` job (`python3 -m pytest tests -q`) picks up `tests/test_fleet_log.py` automatically.
- `autoroute` job: `bash scripts/autoroute_dev.sh` remains green; after the integrator hooks land,
  `.autoroute-dry/meta/logs/node1/<today>.jsonl` exists after the dry-run (integrator may add an
  `ls` assertion to `scripts/autoroute_dev.sh`; requested, not required for this item).
- `static_gates`: no change (module lives outside `public/`).
- Import smoke suggestion for `ci.yml` (integrator): `python3 -c "import iot_asp_autoroute.fleet_log as f; assert f.RECORD_KEYS[0]=='kind'"`.
- Static grep in this test file: `fleet_log.py` source contains no `import numpy`, `import scipy`,
  and no top-level `from google.cloud`.

## Retention / aggregation (Colab handoff — #17, #26)

`retention_plan()` returns exactly this structure (values are the contract; wording may differ):

| Layer | Prefix | Format | Producer | Consumer | Retention | Mechanism |
|-------|--------|--------|----------|----------|-----------|-----------|
| Raw fleet logs | `meta/logs/<node>/<YYYY-MM-DD>.jsonl` (+ `.part.jsonl` fallbacks) | JSON Lines, UTF-8, one `fleet_log` record per line, fixed key order | ADK `tools.py` (`ingest_telemetry`, `process_sudden_freq`) | Colab ETL (#17/#26), `fleet_log_summary` tool | **30 days** | GCS lifecycle `Delete`, `condition.age = 30`, `matchesPrefix = ["meta/logs/"]` |
| Daily aggregates | `meta/logs-agg/<node>/<YYYY-MM-DD>.json` | one `aggregate_records` object (`window_s = 300`) | Colab ETL nightly (`03:30 America/New_York`, i.e. after the night window closes; cron in UTC per DST) or `fleet_log_summary` on demand | Gemini Enterprise seats via features; dashboards | **365 days** | GCS lifecycle `Delete`, `condition.age = 365`, `matchesPrefix = ["meta/logs-agg/"]` |
| Features | `meta/features/<node>/…` | existing `iot_asp_features` JSON (`colab_etl.extract_features`) | Colab only | ADK / Gemini (never authoritative) | governed by #17 | unchanged |
| Patches | `meta/patches/<node>.json` | — | ADK `write_patch` only | phones | n/a | **Colab/ETL never writes here** |

Lifecycle JSON emitted by `retention_plan()["lifecycle"]` (apply with `gcloud storage buckets update
gs://$IOT_ASP_GCS_BUCKET --lifecycle-file=…`; bucket name from env, never in git):

```json
{"rule": [
  {"action": {"type": "Delete"}, "condition": {"age": 30,  "matchesPrefix": ["meta/logs/"]}},
  {"action": {"type": "Delete"}, "condition": {"age": 365, "matchesPrefix": ["meta/logs-agg/"]}}
]}
```

Colab handoff contract:

- Colab reads `meta/logs/<node>/*.jsonl` with `userdata` refs only (`GCP_SA_JSON`,
  `IOT_ASP_GCS_BUCKET`), tolerating unknown trailing keys and skipping malformed lines exactly as
  `read_log_records` does (shared function — import `iot_asp_autoroute.fleet_log`, do not re-implement).
- Colab computes daily aggregates with the **same** `aggregate_records` (pure, stdlib) and writes
  `meta/logs-agg/`; it may also project `nightNY`, `lfGate`, `band`, `power` into
  `meta/features/` rows (columns already declared in `colab_etl.TELEMETRY_FEATURE_COLUMNS`).
- Aggregates are the long-lived artefact; raw logs are ephemeral. Study material and any PII stay in
  gitignored `study/` and never enter `meta/logs/`.
- Soft-delete: `Delete` moves objects to soft-deleted state for the bucket's soft-delete retention
  (default 7 days) before hard deletion — budget accordingly; no restore path is promised.

## Risks / HW limits

- **GCS has no append.** Read-modify-write per record is O(file size) and racy under concurrent
  ingest from three phones; `if_generation_match` + 3 retries + `.part.jsonl` fallback bounds the loss
  to zero records at the cost of occasional side-files. If ingest rate exceeds ~1 record/s per node,
  switch to per-record objects (`meta/logs/<node>/<date>/<ts>.json`) and let Colab concatenate — the
  `read_log_records` interface stays the same. Not needed for the 2–5 s beacon cadence.
- **Date partition is UTC** (consistent with wire timestamps), while `nightNY` is local. A NY night
  spans two UTC files; the aggregator is date-agnostic so `fleet_log_summary(node, date)` for a NY
  night should be run over two UTC dates by the caller (documented in the tool docstring).
- **`zoneinfo` needs tzdata.** CPython 3.11/3.12 on Linux CI uses the system tz database; the
  `America/New_York` key was verified importable here. If a slim container lacks tzdata, `ZoneInfo`
  raises `ZoneInfoNotFoundError` at import. `fleet_log` catches it and falls back to
  `nightNY = False` plus a one-time `warn` record (`event="tz_unavailable"`); it must **not** ship a
  hand-rolled EST/EDT table. If that ever fires, the integrator adds `tzdata` to `requirements.txt`.
- **Phone-side `nightNY`** may disagree with server (phone clock skew / wrong tz). Server value wins in
  the log; the phone value is not persisted separately.
- **Beacon fields not yet in `public/index.html` on this checkout** — enrichment does not depend on
  them; when the owner's Mac lands the beacon change, keys must be additive and go through
  `scrub_pii` like everything else.
- No hardware limits are introduced; band tags describe policy, not capability. LF `10-20` remains
  gated by `lfDriveCapable` in the clamp layer; Safari + BT cannot produce true infrasound.

## Sources

- Context7 `/python/cpython` — `zoneinfo.ZoneInfo(key)` (IANA keys, DST/fold handling via `fromutc`),
  `datetime.astimezone(tz)`, `datetime.fromtimestamp(ts, timezone.utc)`, and the 3.11 note that
  `datetime.fromisoformat()` parses most ISO-8601 forms.
- Context7 `/googleapis/python-storage` — `Blob.upload_from_string(data, content_type=…,
  if_generation_match=…)` ("overwrites existing content by default"), `download_blob_to_file` /
  `BlobReader` `if_generation_match` download kwargs, and `transfer_manager.upload_many`
  `skip_if_exists` implemented as `if_generation_match = 0` → `412 Precondition Failed`.
- https://docs.cloud.google.com/storage/docs/objects — "Objects are immutable, which means that an
  uploaded object cannot change throughout its storage lifetime" (why live mode is read-modify-write).
- https://docs.cloud.google.com/storage/docs/request-preconditions — `ifGenerationMatch` semantics,
  `412 Precondition Failed` on mismatch.
- https://docs.cloud.google.com/storage/docs/lifecycle — `Delete` action, `age`, `matchesPrefix`
  conditions, soft-delete default 7 days after lifecycle `Delete`.
- https://docs.cloud.google.com/storage/docs/json_api/v1/buckets — `lifecycle.rule[].action.type`
  (`Delete`), `condition.age` (days), `condition.matchesPrefix` (list of strings).
- https://jsonlines.org/ — JSON Lines: UTF-8, one JSON value per line, `\n` separated.
- GitHub issues #22 (scope), #17 (Colab pipeline, closed), #26 (Colab live GCS → `meta/features` only,
  never `meta/patches/`) — read via the GitHub connector on 2026-09-08.
- Repo: `CLAUDE.md`, `.claude/rules/{autoroute-backend,docs-and-specs,ci-and-workflows,public-frontend}.md`,
  `docs/api-contract.md`, `docs/DESIGN_CONSTRAINTS.md`, `docs/autoroute.md`, `docs/ci.md`,
  `docs/colab-gemini-pipeline.md`, `docs/awesome-iot-asp.md` (file:line cites above).
