# #10 / #11 — React / React Strict DOM rewrite + React-era multi-device fleet polish

Issues: https://github.com/team-project-pikachu/IoT-ASP/issues/10 · https://github.com/team-project-pikachu/IoT-ASP/issues/11 · Milestone: M0 (tracking only) · Labels: `enhancement`, `parked`
Related: [01-m0-public-blaster.md](01-m0-public-blaster.md) (the static app this would replace), [27-continuous-ship-dev-test-prod.md](27-continuous-ship-dev-test-prod.md) (Vercel pipeline).

## Status

**Parked — constraints only.** The issue text is the product decision: "Optional rewrite of static
`public/index.html` to React / React Strict DOM. Do not block shipping the static blaster." #11 (device
cards, seed compare, fleet health) depends on #10. This spec does not schedule the rewrite; it records the
invariants any rewrite must preserve, the build-shape that keeps the repo rules intact, and the
acceptance gates that would prove the rewrite is behaviour-identical. No React / RSD code lands with it.

## M0 deferral (authoritative)

**Decision:** #10 is **out of M0 ship scope**. Milestone M0 tracks the static hop ultrasonic PWA
(all-blast, incoherent hops, 1 iPhone ↔ 1 Soundcore 2, Vercel public URL). The React rewrite is
optional polish and must not block closing M0.

| Criterion | M0 outcome |
|-----------|------------|
| Ship path | Static `public/index.html` only (no `web/` package, no npm at repo root) |
| Issue #10 | Keep `parked` / close as deferred from M0 tracking — **do not** implement rewrite for M0 |
| Issue #11 React cards | Blocked on #10; static fleet strip already on `main` (see #11 note) |
| Milestone closeout | Remove #10 (and React portion of #11) from milestone/1 once this deferral is recorded |

**Unpark #10 only when all of the following are true:**

1. Static blaster has field acceptance on ≥3 phones (`#62`) and Vercel prod URL is stable.
2. `public/index.html` has outgrown maintainability (owner judgment) **or** a native shell (#9 / #41)
   needs shared RSD components — not before.
3. Owner Mac clone is not ahead of `origin/main` on `public/index.html` (merge-friction risk in Risks).
4. A dedicated `web/` scaffold PR lands parity first (Acceptance tests below) before any UX churn.

Until then: no React scaffold, no StyleX/RSD dependency, no `deploy.yml` `web_build` job.

## Goal

If (and only if) the fleet UI outgrows one file, rebuild `public/` as a React app — optionally with
**React Strict DOM** (RSD) so the same components could later run in a native shell (#9) — while keeping
**every** wire, safety and deployment invariant of the static blaster, and then add the #11 fleet polish:
a card per device (`deviceId`, `seed`, `seedSource`, `algo`, `vibClass`, watchdog counters), a seed
compare view (three phones, incoherence check), and a fleet-health strip (`lastHopAgeMs`, `ctxResumes`,
`watchdogTrips`, patch status).

## Prior art

- **This repo:** single-file vanilla PWA at `public/index.html` — the only ship surface for M0.
- **Sibling `hop-ultrasonic`:** also a static `public/index.html` PWA (no React app); useful for
  UX/copy parity, not a React migration target.
- **React Strict DOM:** upstream still documents native as work-in-progress; web output would be
  the only shippable RSD surface if unparked (see Sources).
- **No prior React scaffold** exists in this repository (`web/` package absent on `main`).

## Shipped on `main`

Verified by reading `origin/main` @ `ddb6c7b` (2026-09-08) and the rules:

| What | Where |
|------|-------|
| Single-file PWA: CSS + HTML + one IIFE script; no bundler, no npm at repo root; Vercel serves `public/` statically | `public/index.html` (~2848 lines / ~135 kB on `main`); `vercel.json`; `.claude/rules/public-frontend.md:9` |
| Literals CI asserts: `Hold / Manual` label, `holdManual` wire key, `holdPatchBtn` id, `SCHEMA_VERSION = 1` | `scripts/ci_static_gates.sh` + `public/index.html` |
| Patch path order: `pollPatch()` → `applyPatch()` → `clampPatch()`; Hold short-circuits both | `public/index.html` (Hold / Manual path) |
| Web Audio rules: gesture unlock, 48 kHz, mic constraints AEC/NS/AGC off, never route mic to output | `.claude/rules/public-frontend.md:15`; `docs/iphone-bluetooth.md` |
| Per-tab seed (`mulberry32`), no shared seed; `localStorage` keys `hop.*` | `public/index.html`; rule `:16` |
| Telemetry payload = device metrics only, additive under `schemaVersion: 1` | `public/index.html`; `docs/api-contract.md` |
| No keys / ADK / Vertex in `public/`; static gate greps `AIza…`, `sk-…`, `PRIVATE KEY`, `apiKey:` | `scripts/ci_static_gates.sh`; `CLAUDE.md` invariant 3 |
| Static HTML tests + Playwright smoke exist for the current file | `tests/test_public_html.py`, `tests/e2e/` |
| Ship pipeline: gates → dev (Vercel preview) → test (smoke) → prod | `.github/workflows/deploy.yml`, `docs/deploy.md` |
| Static multi-device fleet strip (M0-compatible #11 slice): seed compare, Simulate impulse, peer cards | `fleetSeedCompare`, `simImpulseBtn`, fleet panel in `public/index.html` (landed via Balanced PR2 / #66) |

## Remaining scope (constraints a rewrite must satisfy)

1. **Repo shape:** the source lives in a new top-level `web/` package (`package.json`, lockfile, Vite or
   equivalent); the **build output** is written to `public/` (still the Vercel root per `vercel.json`).
   `public/patch.json`, `public/README.txt` and the PWA manifest are copied through unchanged.
   Repo root stays npm-free (`.claude/rules/public-frontend.md:9`); `web/` is the only Node project.
2. **Behaviour parity, byte-level where CI greps:** the built `public/index.html` must still contain the
   literals `Hold / Manual`, `holdManual`, `holdPatchBtn`, `SCHEMA_VERSION = 1` (or a build-time constant
   that renders to that exact text), the entropy-seed functions of spec 02 and the watchdog of spec 03 —
   `tests/test_public_html.py` runs against the **built** file.
3. **Web Audio and sensors** stay in plain modules (`audio.ts`, `motion.ts`) invoked from React effects;
   the audio graph is created once per gesture unlock, never re-created on re-render. DeviceMotion
   permission request remains inside a click handler.
4. **No Web Bluetooth, no device picker, no keys**: the static gate runs against the build; a rewrite that
   pulls a BLE library fails CI (C1, `docs/DESIGN_CONSTRAINTS.md`).
5. **RSD specifics** (if used): components use the `html.*` export and `css.create()` styles; RSD styles
   must be compiled by the StyleX Babel plugin at build time (`@stylexjs/babel-plugin`) — with Vite 8 /
   `@vitejs/plugin-react@6` that means routing the RSD `babel-preset` through `vite-plugin-babel`, otherwise
   the build succeeds but the first styled render throws "Unexpected 'stylex.create' call at runtime".
   RSD is documented as work-in-progress for native; the web output is what ships.
6. **#11 fleet polish** (after parity): a `FleetPanel` fed only by the device's own telemetry plus an
   optional read-only fleet feed (`?fleet=<URL>` to a backend-published `meta/fleet/latest.json` — new,
   backend-owned, never `meta/patches/`); cards show `deviceId`, `seed`/`seedSource`, `algo`, `vibClass`,
   `band`, `lastHopAgeMs`, `ctxResumes`, `watchdogTrips`, `logSeq`; seed compare flags two devices with
   equal `seed`; health strip colours from `lastHopAgeMs` thresholds (spec 03).
7. **Pipeline:** `deploy.yml` gains a `web` build step (`npm ci && npm run build` in `web/`) before
   `vercel build`; pins exact versions; no network at test time.

## Wire fields

None new for #10. For #11 the fleet panel **reads** existing telemetry names only (`deviceId`, `seed`,
`algo`, `vibClass`, `band`, `power`, `nightNY`, `lastHopAgeMs`, `ctxResumes`, `watchdogTrips`, `logSeq`,
`logTail`). The optional `meta/fleet/latest.json` aggregate is a backend artefact (fields = the telemetry
names above per device, PII-scrubbed by `fleet_log.scrub_pii`), documented in `docs/api-contract.md` when
it exists — integration request, not part of this spec.

## Clamps / safety

- All phone clamps (`VOL_PATCH_MAX = 12`, `BAND_ABS_LO/HI`, `clampPatch` ranges at `index.html:522`,
  `:1375-1388`) move verbatim into a `clamps.ts` module with the same numbers and unit tests.
- Hold / Manual: `applyPatch` and `pollPatch` short-circuit **before** any state update; React state must
  never apply a patch through a render path that bypasses `clampPatch`.
- Telemetry stays device-metrics-only; no React analytics, no third-party scripts, no fonts from CDNs
  that would leak fleet IPs beyond Vercel.
- Seeds remain per tab; the fleet panel compares seeds, it never shares one.
- No secrets in `web/` config; Vercel env names only (`VERCEL_TOKEN`, … per spec 27).

## Acceptance tests

1. Parity: `tests/test_public_html.py` (specs 01/02/03 assertions) passes unchanged against the **built** `public/index.html`.
2. Parity: `tests/e2e/public_smoke.spec.mjs` passes against the built app (`getState()` hook preserved).
3. `bash scripts/ci_static_gates.sh` passes on the built output (Hold/Manual, no keys, `patch.json` `schemaVersion: 1`).
4. `grep -rn "bluetooth\|requestDevice" web/src public/index.html` → empty (C1).
5. Build determinism: two `npm run build` runs produce identical `public/index.html` (or identical hashed bundle set).
6. #11: with a fixture fleet feed of three devices, two sharing a seed, the seed-compare view renders a warning; health strip turns red when `lastHopAgeMs > 5000`.
7. Bundle budget: shipped JS ≤ 150 kB gzipped (static `public/index.html` is ~135 kB uncompressed on `main` @ `ddb6c7b`); measured in CI and printed as a `::notice`.

## CI gate

- `static_gates` + `tests` (against build output) block; `deploy.yml` builds `web/` before `vercel build`.
- A new `web_build` job (`npm ci`, `npm run build`, `npm test`) with pinned Node; no network in tests.

## Risks / HW limits

- A rewrite re-touches the audio-unlock and A2DP-timing paths that took real-device testing; regressions
  are only visible on iPhones (Safari), not in Chromium e2e — keep the static file deployable until parity
  is proven on all three phones.
- RSD's native promise is not a reason to rewrite: the native path (#9) needs `AVAudioSession`, which no
  React layer provides.
- Merge-friction: the owner's Mac clone edits `public/index.html` directly; a generated `public/` turns
  every Cursor edit into a conflict. Do not start #10 while the Mac is ahead of `origin/main` on that file.
- Bundle size and hydration cost on an iPhone 14 running for hours matter more than DX.

## Sources

- GitHub issues #10, #11 (read via the GitHub connector, 2026-09-08).
- Firecrawl developer search → `react/react-strict-dom` README and website docs (`packages/website/docs/learn/index.md`
  "Work in progress — not all capabilities are available on native yet"; `html` export, `css.create()`,
  `style` prop accepts only `css`-created styles; MIT), `learn/environment-setup/03-vite.md` (Vite 8 /
  `@vitejs/plugin-react@6` dropped Babel → use `vite-plugin-babel` for the RSD `babel-preset`, otherwise the
  runtime error "Unexpected 'stylex.create' call at runtime. Styles must be compiled by '@stylexjs/babel-plugin'").
- Repo: `.claude/rules/public-frontend.md`, `docs/DESIGN_CONSTRAINTS.md`, `docs/api-contract.md`,
  `docs/specs/01-m0-public-blaster.md`, `02-…`, `03-…`, `27-…`, `public/index.html` (`origin/main` @ `0625e91`).
