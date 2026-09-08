# #1 — M0: Public Vercel hop blaster (shipped) + telemetry fields (#22) + M0 polish

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/1 · Milestone: M0 · Branch: `claude/mdc-conversion-features-gu3yzk`
Companion specs (same work item, same owned files): [02-max-entropy-seeds.md](02-max-entropy-seeds.md) (#2), [03-continuous-monitoring-watchdog.md](03-continuous-monitoring-watchdog.md) (#3), backend side of the log/telemetry tags in [22-structured-fleet-logs.md](22-structured-fleet-logs.md) (#22).

## Status

**Shipped** — the static PWA is live at **https://hop-ultrasonic-1digital-design.vercel.app/** (source mirror `public/`,
served statically per `vercel.json`). This spec (a) records the live URL and fleet so #1 can be closed, (b) defines the
M0 polish that lands in this branch: the phone-side **telemetry enrichment fields** from #22 (`band`, `power`, `nightNY`,
`lfArmed`, `lfDriveCapable`, `logSeq`, `logTail`, plus the #3 health counters), a **structured monitor log ring buffer**
with a *Copy log JSON* button, a **read-only debug hook** for browser tests, and the first **static + e2e test gates** for
`public/index.html`. Everything is additive under `schemaVersion: 1`.

Fleet (generic, no site PII): **three iPhones — 2 × iPhone 16 + 1 × iPhone 14** — each paired 1:1 over **iOS native
Bluetooth A2DP** to its own Soundcore 2 (C1). Optional third role: chair-mounted for structure-borne / accelerometer bias.

## Goal

1. Close the M0 loop: live URL + fleet recorded in `public/README.txt` and here; all three phones can open the URL, tap
   *Signal on*, and blast concurrently with incoherent per-device hops.
2. Make the heartbeat self-describing for the backend log layer (#22): the phone emits `band`, `power`, `nightNY`,
   `lfArmed`, `lfDriveCapable` and a short structured log tail, so `fleet_log.enrich_telemetry` receives the tags
   directly instead of always inferring them.
3. Make the phone testable without hardware: a deterministic static test (`tests/test_public_html.py`) and a Playwright
   smoke (`tests/e2e/`) that drive the real single-file app in headless Chromium.

## Shipped on `main`

Verified by reading `public/index.html` on this checkout (`origin/main` @ `0625e91`; line numbers exact):

| What | Where |
|------|-------|
| Single IIFE script (exactly one `<script>` tag) | `public/index.html:428` (`grep -c "<script"` = 1) |
| `SCHEMA_VERSION = 1` and backend endpoint constants (no keys) | `public/index.html:435-441` |
| `Hold / Manual` button, id `holdPatchBtn` | `public/index.html:326`; const `:464`; click handler `:1448-1454` |
| Hold short-circuits `applyPatch` and `pollPatch` | `public/index.html:1391`, `:1430` |
| Telemetry section banner `// ══ telemetry beacon + param patch poll ══` (new blocks go right after it) | `public/index.html:1303` |
| `monLog(msg)` — DOM-only log, 40-line cap, no structured records | `public/index.html:1304-1313` |
| `updateTelUI()` fills the Monitor grid | `public/index.html:1315-1330` |
| `telemetryPayload()` — device metrics only; **no** `band`/`power`/`nightNY`/`lf*`/log fields yet | `public/index.html:1332-1360` |
| `beaconTelemetry()` → `navigator.sendBeacon` / `fetch keepalive`; every 2 s | `public/index.html:1362-1373`, `:1456` |
| `clampPatch()` with phone-side `VOL_PATCH_MAX = 12` | `public/index.html:522`, `:1375-1388` (vol clamp at `:1382`) |
| `applyPatch()` (schemaVersion additive, `seedAction: "reseed"` path) | `public/index.html:1390-1427` (reseed `:1409-1414`) |
| Monitor section, `mon-grid` cells `telDevice … telSudden`, `#monLog` | `public/index.html:351-369` |
| Systems-check section + `systemsCheck()` rows (`Hop RNG`, `Telemetry`, `Patch hold`) | `public/index.html:224-243`, `:1498-1554` (RNG row `:1548`) |
| Audio unlock on gesture, 48 kHz request | `public/index.html:779-782`, `:787` |
| Output slider `id="vol" min="0" max="60"` | `public/index.html:344` |
| Offline mock patch `schemaVersion: 1`, `vol: 100` | `public/patch.json` |
| `public/README.txt` — fleet text says "two phones", **no live URL** | `public/README.txt` (12 lines) |
| CI static gates on the literals above + key regexes | `scripts/ci_static_gates.sh:16-18`, `:21-49` |
| `docs/api-contract.md` telemetry rows for the new fields already present in the integrator's working tree (uncommitted) | `docs/api-contract.md:80-85` |
| `tests/test_public_html.py`, `tests/e2e/` | **absent** on this checkout (referenced by `.claude/rules/public-frontend.md:36`) |

## Remaining scope

All code edits are **additive** and live in delimited blocks placed immediately after the banner at
`public/index.html:1303`, in this order: `// ══ structured monitor log (#22) ══`, `// ══ telemetry enrichment (#22) ══`,
`// ══ watchdog (#3) ══` (spec 03), `// ══ max-entropy seeds (#2) ══` (spec 02), `// ══ debug hook (#1) ══`.
Existing ids, literals and clamps are untouched.

### A. Structured monitor log (`// ══ structured monitor log (#22) ══`)

- `const LOG_MAX = 200; const records = []; let logSeq = 0;`
- `function monLog(msg, event, fields, level)` **replaces** the one-argument body at `:1304-1313` while staying
  backward compatible: `monLog("text")` behaves exactly as before for the DOM (prepend, 40-line DOM cap) **and**
  additionally pushes `{seq: ++logSeq, ts: new Date().toISOString(), level: level || "info", event: event || "log",
  msg: String(msg).slice(0, 240), fields: fields && typeof fields === "object" ? fields : {}}` onto `records`,
  dropping from the front when `records.length > LOG_MAX`. `level` ∈ `{debug, info, warn, error}`; anything else →
  `"info"`. Because the replacement is a same-named function declaration in the same scope, all existing callers
  (`:1395`, `:1413`, `:1424`, `:1452`, …) keep working — no caller edits.
- `fields` is caller-supplied device data only (numbers, short enums, ids). Never `navigator.userAgent`, never free
  text from the network (`rationale` stays in `msg`, already truncated).
- Monitor section gains two buttons next to `#monLog` (inside the existing `<section class="mon" id="monitor">`,
  before the `mon-log` div): `<button type="button" class="tap" id="copyLogBtn">Copy log JSON</button>` and
  `<button type="button" class="tap" id="reseedBtn">Reseed</button>` (reseed behaviour in spec 02).
  `copyLogBtn` click → `JSON.stringify(records)` → `navigator.clipboard.writeText(json)` when
  `navigator.clipboard && window.isSecureContext`; on rejection or absence, fallback: create a hidden read-only
  `<textarea>`, set its value, `select()`, `document.execCommand("copy")` best-effort, remove it; either way
  `monLog("log copied", "ui", {n: records.length})`.

### B. Telemetry enrichment (`// ══ telemetry enrichment (#22) ══`)

`telemetryPayload()` at `:1332-1360` is **extended** (the object literal gains keys after `holdManual`; nothing removed
or renamed):

| Key | Value |
|-----|-------|
| `band` | `(+fMin.value <= 100) ? "10-20" : "17-23k"` (mirrors `clamps.band_limits`, `fMin <= 100` rule) |
| `power` | `"ac120"` (constant; fleet is continuous 120 V AC) |
| `nightNY` | `nightNYNow()` — see below; boolean, `false` on any error |
| `lfArmed` | `false` (web fleet never arms LF) |
| `lfDriveCapable` | `false` (Safari + BT cannot drive 10–20 Hz; physics honesty) |
| `lastHopAgeMs` | spec 03 |
| `ctxResumes` | spec 03 |
| `watchdogTrips` | spec 03 |
| `logSeq` | `logSeq` (last sequence number issued, `0` when none) |
| `logTail` | `records.slice(-3)` (array of ≤ 3 records, newest last) |

`function nightNYNow()`:
```js
try {
  const parts = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", hour: "numeric", hour12: false }).formatToParts(new Date());
  const h = parseInt((parts.find(p => p.type === "hour") || {}).value, 10) % 24;   // "24" (h24 ICU quirk) → 0
  return Number.isFinite(h) && (h >= 22 || h < 7);
} catch (_) { return false; }
```
The `% 24` guard exists because `hour12: false` may resolve to the `h24` cycle on some ICU builds and print midnight as
`"24"` (see Sources). `parseInt` of `NaN` → `false`. The backend always recomputes `nightNY` from `ts`
(`fleet_log.enrich_telemetry`), so the phone value is advisory.

### C. Debug hook (`// ══ debug hook (#1) ══`)

```js
window.__hop = Object.freeze({
  telemetryPayload,
  getLog:   () => records.slice(),
  getState: () => ({ running, holdManual, algo, seed, seedSource })
});
```
Read-only (frozen object, functions return copies); exposes no URLs, tokens, or DOM. `seedSource` is defined in
spec 02 (`'stored' | 'entropy'`). It exists so the Playwright smoke can assert behaviour without scraping the DOM.

### D. `public/README.txt` (M0 record)

Add, keeping the existing text: `Live: https://hop-ultrasonic-1digital-design.vercel.app/` and
`Fleet: 3 phones — 2× iPhone 16 + 1× iPhone 14, each 1:1 to its own Soundcore 2 over iOS native Bluetooth (A2DP).
No Web Bluetooth.` Update "two phones" wording to "the fleet phones (three)". No addresses, no seat emails.

### E. Tests

- `tests/test_public_html.py` (stdlib only: `pathlib`, `re`, `html.parser`) — see *Acceptance tests* 1–12.
- `tests/e2e/` — Playwright smoke; see *Acceptance tests* 13–19 and *CI gate*.
  - `tests/e2e/package.json`: `{"name": "iot-asp-e2e", "private": true, "devDependencies": {"@playwright/test": "1.56.1"}}`
    plus `"scripts": {"test": "playwright test"}`. **Pin rationale:** the registry latest at spec time is `1.63.0`
    (published 2026-09-04), but its `browsers.json` requires Chromium revision **1243**; this environment pre-installs
    `/opt/pw-browsers/chromium-1194` + `chromium_headless_shell-1194`, which is the revision shipped by `playwright-core`
    **1.56.1** (globally installed here) and `npx playwright install` is forbidden. `1.56.1` is therefore the exact
    version that runs offline here. Bumping it requires refreshing `/opt/pw-browsers` (or CI's cache) in the same change.
  - `tests/e2e/run.sh`: `#!/usr/bin/env bash`, `set -euo pipefail`, `ROOT` from its own path,
    `export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-/opt/pw-browsers}"`, `cd "$ROOT/tests/e2e"`,
    `npm ci || npm i`, start `python3 -m http.server 8765 --directory ../../public --bind 127.0.0.1 &` (trap to kill on
    exit), wait until `curl -sf http://127.0.0.1:8765/index.html` (≤ 20 × 0.25 s), `npx playwright test`, print
    `OK e2e` on success and exit with Playwright's code otherwise.
  - `tests/e2e/public_smoke.spec.mjs`: `import { test, expect } from "@playwright/test"`; `test.use({ baseURL:
    "http://127.0.0.1:8765" })`; one `test.describe("public blaster smoke")`. Uses `page.evaluate(() => window.__hop…)`.
    Clipboard is **not** asserted (needs permissions) — only that `#copyLogBtn` exists and clicking it does not throw.
  - `tests/e2e/.gitignore`: `node_modules/`, `test-results/`, `playwright-report/`, `package-lock.json` is **kept**
    (committed) so `npm ci` is reproducible.

## Wire fields

All additive under `schemaVersion: 1`; canonical rows already exist in `docs/api-contract.md:80-85` (working tree).
Phone emits every heartbeat (2 s cadence, `:1456`):

| Field | Type | Phone value | Backend treatment |
|-------|------|-------------|-------------------|
| `band` | string | `"17-23k"` unless `fMin ≤ 100` → `"10-20"` | `enrich_telemetry`: explicit valid tag wins |
| `power` | string | `"ac120"` | passthrough tag |
| `nightNY` | bool | NY hour ∈ [22,24) ∪ [0,7) via `Intl` | recomputed from `ts` (advisory) |
| `lfArmed` | bool | `false` | passthrough |
| `lfDriveCapable` | bool | `false` | passthrough; gates LF band in clamps |
| `lastHopAgeMs` | number | spec 03 | health counter |
| `ctxResumes` | number | spec 03 | health counter |
| `watchdogTrips` | number | spec 03 | health counter |
| `logSeq` | number | last log sequence issued | observability |
| `logTail` | array ≤ 3 | `{seq, ts, level, event, msg, fields}` | observability; **goes through `scrub_pii`** like every key |

No patch fields change. `seedSource` is UI/debug only and **not** on the wire.

## Clamps / safety

- `VOL_PATCH_MAX = 12` (`:522`), `BAND_ABS_LO/HI`, `clampPatch()` and the `Hold / Manual` short-circuits are **not
  modified**. `SCHEMA_VERSION = 1` unchanged. No `navigator.bluetooth` anywhere (C1). No key-like strings
  (`AIza…`, `sk-…`, `PRIVATE KEY`, `*_API_KEY=`, `apiKey:`) — the structured log must never store a URL query string
  (`?telemetry=` could carry a token by a careless operator): `fields` are numbers/enums only, `PATCH_URL` is logged
  as before via `monLog` text only.
- `lfArmed`/`lfDriveCapable` are hard-coded `false` on the web fleet; the backend LF gate (`priors.lf_drive_capable`)
  therefore never opens from a browser heartbeat.
- **Known clamp drift — owner decision, not changed here:** `docs/api-contract.md:77` says vol "UI percent 0–12";
  `docs/api-contract.md:128` says "soft ≤12, hard refuse >20"; `clamps.py:20-21` is `vol_soft_max == vol_hard_max ==
  100.0`; the phone clamp `VOL_PATCH_MAX = 12` (`:522`); the slider max is `60` (`:344`); the mock `patch.json` sends
  `vol: 100` (clamped to 12 on the phone). Four different ceilings coexist. This spec preserves all of them and adds
  a static test that asserts `VOL_PATCH_MAX = 12` **as-is** so any change is deliberate. Recommended resolution
  (for the owner): pick one number, update `api-contract.md` rows + `clamps.py` + `VOL_PATCH_MAX` + slider in one PR
  referencing #1, and update the test constant then.
- PII: `logTail.msg` is backend/UI-authored text truncated to 240 chars; `fields` never contain UA strings, URLs,
  geolocation, or names. Telemetry stays "device metrics only" (`public-frontend.md:31`).

## Acceptance tests

`python3 -m pytest tests/test_public_html.py -q` (stdlib only, no network, reads `public/index.html` and
`public/README.txt` from the repo root resolved relative to the test file):

1. Literals present: `Hold / Manual`, `holdManual`, `holdPatchBtn`, `SCHEMA_VERSION = 1` (regex `const SCHEMA_VERSION = 1;`),
   `VOL_PATCH_MAX = 12` (regex `const VOL_PATCH_MAX = 12,`).
2. New ids present as `id="…"`: `copyLogBtn`, `reseedBtn`, `telHopAge`, `telResumes`, `telWatchdog`; existing ids
   still present: `telDevice`, `telSeed`, `telAlgo`, `telPeak`, `telAccel`, `telMic`, `telVib`, `telHold`,
   `telSudden`, `monLog`, `sysList`, `sysBtn`, `vol`, `fMin`, `fMax`.
3. The `telemetryPayload` function body (text from `function telemetryPayload(){` to the next `\n  }\n`) contains the
   tokens `band`, `power`, `nightNY`, `lfArmed`, `lfDriveCapable`, `lastHopAgeMs`, `ctxResumes`, `watchdogTrips`,
   `logSeq`, `logTail`, `holdManual`, `schemaVersion: SCHEMA_VERSION`.
4. `"ac120"` and `"America/New_York"` and `"10-20"` and `"17-23k"` literals present.
5. Delimited blocks present: `// ══ structured monitor log (#22) ══`, `// ══ telemetry enrichment (#22) ══`,
   `// ══ watchdog (#3) ══`, `// ══ max-entropy seeds (#2) ══`, `// ══ debug hook (#1) ══`; `LOG_MAX = 200`;
   `window.__hop`.
6. Negative: `navigator.bluetooth` absent; `requestDevice(` absent; none of the CI key regexes
   (`AIza[0-9A-Za-z_-]{20,}`, `sk-[A-Za-z0-9]{20,}`, `BEGIN (RSA |OPENSSH )?PRIVATE KEY`,
   `(GOOGLE|GEMINI|VERTEX)_API_KEY\s*[:=]\s*['"]`, `apiKey\s*[:=]\s*['"][A-Za-z0-9_-]{16,}['"]`) match.
7. HTML parses with `html.parser` (`HTMLParser` subclass counting start tags; no exception) and the count of
   `<script` start tags is exactly **1**; `<html>`, `<head>`, `<body>`, `<main>` each present once.
8. `public/README.txt` contains `https://hop-ultrasonic-1digital-design.vercel.app/`, `iPhone 16`, `iPhone 14`,
   `three`/`3`, `native Bluetooth`; does not contain `@` (no emails) or a 5-digit US ZIP pattern `\b\d{5}\b` and does
   not contain `Web Bluetooth` without a preceding `No `.
9. `public/patch.json` still `schemaVersion == 1` (json.loads).
10. `monLog(` is declared once as `function monLog(msg, event, fields, level)`, and the legacy one-arg calls still exist
    (at least 3 `monLog("` occurrences).
11. Every `// ══ … (#N) ══` banner line in the file matches `^\s*// ══ .+ \(#\d+\) ══+\s*$`.
12. File size guard: `public/index.html` < 120 000 bytes (currently 72 537) — catches accidental duplication.

`bash tests/e2e/run.sh` (headless Chromium from `/opt/pw-browsers`, local `http.server` on 127.0.0.1:8765, no
external network):

13. `page.goto("/")` resolves with status 200 and `document.title` is non-empty; no `pageerror` events are raised
    (collect via `page.on("pageerror")` and assert `[]` at the end).
14. Locators `#holdPatchBtn`, `#copyLogBtn`, `#reseedBtn`, `#telHopAge`, `#telResumes`, `#telWatchdog`, `#monLog`
    are attached; `#holdPatchBtn` text is `Hold / Manual`.
15. `window.__hop.getState().holdManual === false` initially; after `click('#holdPatchBtn')` it is `true` and
    `#holdPatchBtn` has `aria-pressed="true"`; a second click returns it to `false`.
16. `p = window.__hop.telemetryPayload()`: `p.schemaVersion === 1`; `p.band ∈ {"17-23k","10-20"}` and equals
    `"17-23k"` with default sliders; `typeof p.nightNY === "boolean"`; `p.power === "ac120"`; `p.lfArmed === false`;
    `p.lfDriveCapable === false`; `Array.isArray(p.logTail) && p.logTail.length <= 3`;
    `Number.isInteger(p.logSeq)`; `typeof p.holdManual === "boolean"`; `p.deviceId` matches `^dev-[a-z0-9]{8}$`;
    `p.ts` matches `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$`.
17. `seed = window.__hop.getState().seed` is a positive integer (`Number.isInteger(seed) && seed > 0`) and
    `getState().seedSource ∈ {"stored","entropy"}` (equals `"entropy"` on a fresh context).
18. `click('#reseedBtn')` → `getState().seed !== seed` and `localStorage.getItem("hop.seed") === String(newSeed)`;
    `getLog()` contains a record with `event === "reseed"`.
19. `click('#copyLogBtn')` does not throw; afterwards `getLog().some(r => r.event === "ui")`; every log record has
    keys exactly `["seq","ts","level","event","msg","fields"]` and `seq` is strictly increasing.

Exit code of `bash tests/e2e/run.sh` is reported in the implementation notes; if `npm ci`/`npm i` cannot reach the
registry through the proxy, the failure text is reported verbatim and the static tests remain the blocking gate.

## CI gate

- `static_gates` job (`scripts/ci_static_gates.sh`) — unchanged and must stay green: literals, key regexes,
  `patch.json` schemaVersion, clamp constants.
- `tests` job (`python -m pytest tests -q`) picks up `tests/test_public_html.py` automatically (stdlib only; runs on
  3.12). This is the **blocking** gate for `public/` changes.
- Optional `e2e` job (integration request, `.github/workflows/ci.yml`): `actions/setup-node@v4` (node 22),
  `cache: npm`, `cache-dependency-path: tests/e2e/package-lock.json`, then `npx playwright install --with-deps
  chromium` **is** allowed in CI (not locally), then `bash tests/e2e/run.sh`. Marked `continue-on-error: false`
  only once it has been green on `main` twice; until then `continue-on-error: true`. Pin: same `1.56.1`.
- `mdc_check`: unaffected.

## Risks / HW limits

- **Bluetooth codec / DSP roll-off:** Soundcore 2 (12 W, BT 5.0, BassUp) attenuates 17–23 kHz; SBC/AAC A2DP low-pass
  further. The live app cannot measure delivered SPL; `vol` is Web Audio gain, not dB SPL.
- **Safari + BT cannot produce infrasound**; `lfDriveCapable` is hard-coded `false` — never claim LF drive from the
  web fleet.
- **`nightNY` depends on the phone clock and ICU tz data**; a phone with a wrong time zone still reports NY hour via
  `timeZone: "America/New_York"` (tz data is bundled with the engine), but a wrong wall clock skews it — hence
  server recompute.
- **`sendBeacon` payload growth:** `logTail` adds ≤ 3 × ~300 B; heartbeat stays well under the 64 KiB beacon budget.
- **Playwright pin vs. registry latest** (1.56.1 vs 1.63.0): a future bump must ship with a browser cache refresh.
- **Clipboard API** requires a secure context + transient user activation; on `http://127.0.0.1` Chromium treats
  localhost as secure, iOS Safari requires the tap gesture — hence the `execCommand` fallback.
- **Owner's Mac clone is ahead** on `public/index.html`; the delimited blocks after `:1303` keep the merge mechanical.
  If the Mac already added `band`/`nightNY` keys, the merge must keep **one** definition (the test asserts one
  `telemetryPayload` function).

## Sources

- Context7 `/microsoft/playwright` — `PLAYWRIGHT_BROWSERS_PATH` overrides the browser cache location for install
  *and* test runs (`docs/src/browsers.md`); `webServer` plugin options (`command`, `url`, `cwd`, `env`).
- `npm view @playwright/test version` → `1.63.0` (published 2026-09-04T22:44Z); `npm pack playwright-core@1.63.0`
  → `browsers.json` chromium revision `1243` (153.0.8010.12); local `/opt/node22/lib/node_modules/playwright`
  (`1.56.1`) `browsers.json` chromium revision `1194` (141.0.7390.37) = `/opt/pw-browsers/chromium-1194`.
- Context7 `/mdn/content` — `Intl.DateTimeFormat` `hour12: false` example, `formatToParts()` `hour` part,
  `resolvedOptions().hour12` derived from `hourCycle` (`h23`/`h24`); `crypto.getRandomValues()` fills a
  `Uint32Array` and is the only `Crypto` member usable from an insecure context; `navigator.clipboard.writeText()`
  needs a secure context and transient activation.
- https://stackoverflow.com/questions/65604554/intl-datetimeformat-returns-an-hour-over-24 and
  https://github.com/paperclipai/paperclip/issues/7529 — `hour12:false` + `en-US` can resolve to the `h24` cycle and
  print midnight as `"24"` on some ICU versions (why `% 24` is applied). Verified locally on Node 22.22.2 that both
  `hour12:false` and `hourCycle:"h23"` print `"00"` at NY midnight.
- GitHub issues #1, #2, #3, #22 (read via the GitHub connector on 2026-09-08); `CLAUDE.md` (live URL, fleet, drift
  note), `.claude/rules/public-frontend.md`, `.claude/rules/docs-and-specs.md`, `.claude/rules/ci-and-workflows.md`,
  `docs/api-contract.md`, `docs/DESIGN_CONSTRAINTS.md`, `docs/autoroute.md`, `docs/ci.md`, `scripts/ci_static_gates.sh`,
  `services/autoroute-adk/iot_asp_autoroute/clamps.py:20-27` (file:line cites above).
