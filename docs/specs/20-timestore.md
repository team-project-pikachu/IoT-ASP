# #20 — Timestore: SciPy ≥16-parameter fit, 0.0006 s quantum, Fairfax weather prior, cipher tags

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/20 · Labels: `enhancement`, `parked` · Related: `vib_anomaly.py` (1 Hz / 0.0005 g, shipped), [22-structured-fleet-logs.md](22-structured-fleet-logs.md), [26-colab-live-gcs-features.md](26-colab-live-gcs-features.md)

## Status

**Parked — stub exists only on the owner's Mac.** The issue references
`services/autoroute-adk/iot_asp_autoroute/timestore.py` and `docs/timestore.md` ("stub done": 24 h circle,
year horizon, 0.0006 s uniqueness quantum). Neither file is on `origin/main` (`git ls-tree -r origin/main`
has no `timestore*`; `docs/PRIOR_ART.md:22` on this branch records the same gap). This spec pins the
design so the Mac stub and the eventual module converge: the time-feature model, the ≥16-parameter
SciPy fit, the weather-prior source (NWS `api.weather.gov`, no street addresses), the cipher-tag rules,
and how the result feeds `priors` and the structured log. No implementation lands with this spec.

## Goal

1. **Timestore = a per-node time model** that turns wall-clock time into features the autoroute can use
   as priors: position on the **24 h circle** (`sin/cos(2π·hourOfDay/24)`), position on the **year
   horizon** (`sin/cos(2π·dayOfYear/365.25)`), and a **uniqueness quantum of 0.0006 s** so that two
   telemetry points closer than 0.6 ms are the same point (dedupe / ordering key), consistent with the
   existing 1 Hz / 0.0005 g vib quantum.
2. A **non-linear ≥16-parameter SciPy fit** of a disturbance-rate series against those features
   (harmonics of day and year, trend, weather coupling), refit offline (Colab / dry-run), never on the phone.
3. A **Fairfax-area weather prior** from the National Weather Service API (`api.weather.gov`), resolved
   from a coarse grid — **never** a street address — and cached as a small JSON feature.
4. **Cipher hooks**: opaque, non-PII experiment tags that label conditions (e.g. `cipher: "a7f3"`) without
   encoding who/where.
5. Wire the fitted prior into `priors.seismo_bundle()` text and into `fleet_log` records (structured
   telemetry logging, "awesome-inspired").

## Shipped on `main`

Verified by reading the files (backend identical between `origin/main` @ `0625e91` and this branch):

| What | Where |
|------|-------|
| Vib quantum `VIB_QUANTUM = 0.0005` g; 1 Hz series; SciPy `medfilt` + `median_abs_deviation(scale="normal")` + `find_peaks` | `services/autoroute-adk/iot_asp_autoroute/vib_anomaly.py:24-27`, `:93-120` |
| `quantize_vib` / `quantize_series` (round to nearest quantum) — the pattern the 0.0006 s time quantum reuses | `vib_anomaly.py:30-42` |
| Timestamp rules: UTC ISO-8601 `%Y-%m-%dT%H:%M:%SZ`; object names replace `:` with `-`; `parse_ts` / `to_wire_ts` / `night_ny` (`America/New_York`, 22:00–07:00) | `.claude/rules/autoroute-backend.md:16`; `fleet_log.py:106-165` (branch) |
| `nightNY` telemetry tag (local hour in America/New_York ∈ [22, 07)) | `docs/api-contract.md:82` |
| Priors bundle with `docs` pointers and honesty string — the hook point for a time/weather prior | `services/autoroute-adk/iot_asp_autoroute/priors.py:280-295` |
| SciPy pin `scipy>=1.14.0,<1.18`, numpy `>=1.26,<3` | `services/autoroute-adk/requirements.txt:5-6` |
| Colab ETL writes `meta/features/` only, never `meta/patches/` | `.claude/rules/autoroute-backend.md:13`; `features_live.assert_not_patch_path` (branch) |
| No `timestore.py`, no `docs/timestore.md`, no weather code on `origin/main` | `git ls-tree -r --name-only origin/main \| grep -i "timestore\|weather"` → nothing |

## Remaining scope

Module `services/autoroute-adk/iot_asp_autoroute/timestore.py` (numpy + scipy allowed, no network at import
time), tests `tests/test_timestore.py`, doc `docs/timestore.md`.

1. **Quantum + circle features (stdlib + numpy):**
   - `TIME_QUANTUM_S = 0.0006`; `quantize_ts(ts) -> float` rounds epoch seconds to the nearest quantum;
     `time_key(ts) -> str` = quantized epoch as `f"{q:.4f}"` (dedupe key; two points with equal keys are one).
   - `circle_features(ts, tz="America/New_York") -> dict` = `{hodSin, hodCos, doySin, doyCos, nightNY}`
     (hour of day, day of year, both in local time; `nightNY` reuses `fleet_log.night_ny`).
2. **≥16-parameter model (`scipy.optimize.least_squares`):**
   `rate(t) = c0 + c1·τ + Σ_{k=1..4}[a_k sin(2πk·h/24) + b_k cos(2πk·h/24)] + Σ_{k=1..2}[p_k sin(2πk·d/365.25) + q_k cos(2πk·d/365.25)] + w1·windKt + w2·precipProb`
   → 2 + 8 + 4 + 2 = **16 parameters** (`PARAM_NAMES`, fixed order). Fit with
   `least_squares(residuals, x0, bounds=(lb, ub), method="trf", x_scale=..., loss="soft_l1", max_nfev=2000)`;
   bounds keep amplitudes ≤ the series range and `c0 ≥ 0`. Refuse (return `ok=False`) when the series has
   fewer than **48** points (3 points per parameter) — never extrapolate from a night of data. Result is a
   JSON dict `{ok, params, paramNames, cost, n, quantumS, fitted: "scipy.optimize.least_squares/trf"}`.
3. **Weather prior (`weather_prior(grid, fetch=None)`)** — pure function over an injected fetcher (tests pass
   a fake; CI never hits the network):
   - Resolve once: `GET https://api.weather.gov/points/{lat},{lon}` → `properties.gridId` (WFO),
     `gridX`, `gridY`, `forecastHourly` URL. The API accepts at most four decimals; **this project sends
     two** (~1 km), taken from a public county-scale centroid stored as `IOT_ASP_WX_POINT` (env name;
     value never committed). Persist only `{wfo, gridX, gridY}` in `meta/features/wx/grid.json`.
   - Hourly: `GET /gridpoints/{wfo}/{x},{y}/forecast/hourly` with a `User-Agent` header naming the
     project (NWS requires one); take `windSpeed`, `probabilityOfPrecipitation`, `temperature` for the
     current hour → `{windKt, precipProb, tempF, fetchedAt}` cached ≤ 1 h in `meta/features/wx/latest.json`.
   - Failure → `{ok: False, reason}` and the fit runs with `windKt = precipProb = 0` (prior degrades, never blocks).
4. **Cipher hooks:** `cipher_tag(label) -> str` = first 8 hex chars of `sha256(label)` where `label` is an
   operator-chosen experiment name matching `^[a-z0-9_-]{1,32}$`; `validate_cipher(tag)` accepts
   `^[0-9a-f]{8}$` only. Tags are **never** derived from `deviceId`, timestamps, addresses, or names, and
   the label→tag map lives in the gitignored `study/`. Telemetry may carry `cipher` (see Wire fields).
5. **Wiring:** `priors.seismo_bundle()` gains `"timestore": timestore.summary()` (params + `nightNY` +
   weather snapshot, or `{ok: False}`); `fleet_log.log_record` copies `cipher` and `timeKey` when present;
   `features_live.build_feature_record` stores the fit under `meta/features/<node>/timestore-<date>.json`.
   Nothing here writes `meta/patches/`.
6. CLI `python3 -m iot_asp_autoroute.timestore --demo` fits a seeded synthetic 7-day series offline and
   prints the 16 parameters.

## Wire fields

| Field | Direction | Status |
|-------|-----------|--------|
| `ts` | telemetry | existing ★; `time_key(ts)` derived server-side |
| `nightNY` | telemetry / log | existing (#22) |
| `cipher` | telemetry (optional) | **proposed additive** string `^[0-9a-f]{8}$`; integration request against `docs/api-contract.md` |
| `timeKey` | log record only | derived; not sent by phones |
| `priors` | patch | existing list; may include the key `timestore` once `PRIORS["timestore"]` exists |

## Clamps / safety

- The timestore is a **prior**, not a controller: it may re-rank `preferred_algos` and nudge `pulseMs` /
  `shriekMs` **inside** `CLAMPS` (`clamps.py:19-25`); it never touches `vol`, `fMin`/`fMax`, or `algo`
  outside `ALLOWED_ALGOS`. `validate_patch` remains the last word.
- Hold / Manual: `tools.write_patch` still refuses; the timestore never bypasses it.
- **No PII:** two-decimal coordinates from a county-scale centroid, `{wfo, gridX, gridY}` only; no street
  address, no site name, no `deviceId` in any weather object. `cipher` tags are hashes of operator labels
  kept outside git.
- Network access only in the fetcher, only from Colab / the backend, never from `public/` and never in
  tests (fetcher injected).
- Secrets by name: `IOT_ASP_WX_POINT`, `IOT_ASP_GCS_BUCKET`, `GOOGLE_CLOUD_PROJECT`.

## Acceptance tests

`tests/test_timestore.py` (seeded, fixed timestamps, `tmp_path` via `IOT_ASP_AUTOROUTE_DRY_ROOT`):

1. `quantize_ts` maps `1_700_000_000.00029` and `1_700_000_000.00031` to the same key; values 0.0006 apart to different keys.
2. `circle_features("2026-09-08T03:00:00Z")` → `nightNY is True` (23:00 EDT), `hodSin/hodCos` on the unit circle (|·|² = 1 ± 1e-9); `"2026-09-08T15:00:00Z"` → `nightNY is False`.
3. `PARAM_NAMES` has length **≥ 16** and no duplicates.
4. Synthetic series (seed 20, 7 days at 1 h, known coefficients + noise): `fit_rate_model` returns `ok`, recovers `a_1`, `b_1`, `c0` within 10 %, `cost` finite.
5. Fewer than 48 points → `ok is False`, reason mentions the minimum; no exception.
6. `weather_prior` with a fake fetcher returning a points doc then an hourly doc → `{wfo, gridX, gridY}` and `{windKt, precipProb}`; the fake asserts a `User-Agent` header was sent and that the coordinates in the URL have ≤ 2 decimals.
7. `weather_prior` with a failing fetcher → `ok False`, and `fit_rate_model` still fits with zeroed weather columns.
8. `cipher_tag("baseline-a")` is 8 lowercase hex and stable; `validate_cipher("ZZZZ")` is `False`; `cipher_tag("has spaces here")` raises (label regex rejects spaces, so free-text or address-like labels cannot become tags).
9. Negative controls: `holdManual` telemetry never yields a patch from the timestore path; nonsense prior key `"timestore_xx"` is dropped by `filter_prior_keys`.
10. Demo CLI exits 0 offline and prints 16 parameter names.

## CI gate

- `tests` job runs `tests/test_timestore.py` (numpy/scipy already installed via `requirements-dev.txt`).
- `autoroute` job's import smoke gains `iot_asp_autoroute.timestore` (no network at import).
- No live NWS call in CI (`docs/ci.md` § Out of scope: no heavy crawls, no live GCP).

## Risks / HW limits

- `least_squares` with 16 parameters on a few days of 1 Hz-aggregated data is ill-conditioned; the
  `x_scale` and bounds are mandatory, and the minimum-points refusal exists because SciPy will otherwise
  return a "solution" with a huge covariance. SciPy raises `RuntimeError("Optimal parameters not found…")`
  in `curve_fit` when the solver fails; `least_squares` returns `success=False` — the module checks it.
- The weather prior is a **county-scale hourly forecast**, not a site measurement; wind/precip only enter
  as two linear terms and can be zeroed without breaking the fit.
- NWS API availability and rate limits are outside our control; the cache and the degrade path cover it.
- The 0.0006 s quantum is finer than the phone's 1 Hz beacon; it matters only for dedupe/ordering of
  bursty `sendBeacon` retries, not for resolution.
- Any future site-specific time model must stay in `study/`; the public module holds coefficients only.

## Sources

- GitHub issue #20 (read via the GitHub connector, 2026-09-08): "24 h circle + year horizon; uniqueness
  quantum 0.0006 s (stub done); non-linear ≥16-parameter SciPy fit; cipher hooks (non-PII experiment tags);
  Fairfax weather prior (NWS / open meteo — no street addresses)".
- Context7 `/scipy/scipy` — `scipy.optimize.curve_fit` switches to `method="trf"` when bounds are given
  (`lm` refuses bounded problems), renames `maxfev`→`max_nfev` for `least_squares`, raises `RuntimeError`
  on failure, and documents `x_scale` for parameters spanning orders of magnitude; bounds supported since
  SciPy 0.17.
- Firecrawl search → NWS "API Web Service" (https://www.weather.gov/documentation/services-web-API,
  spec 3.11.0 / OAS 3.1): `GET /points/{latitude},{longitude}` → `forecast`, `forecastHourly`,
  `GET /gridpoints/{wfo}/{x},{y}/forecast/hourly`; and api.weather.gov General FAQs
  (https://weather-gov.github.io/api/general-faqs): coordinates limited to four decimals ("about 30 feet");
  two requests (points → gridpoint) by design. A `User-Agent` header is the documented identification
  mechanism (same FAQ / community examples).
- Repo: `vib_anomaly.py`, `priors.py`, `fleet_log.py`, `features_live.py`, `docs/api-contract.md`,
  `.claude/rules/autoroute-backend.md`, `docs/PRIOR_ART.md:22` (records the Mac-only stub).
