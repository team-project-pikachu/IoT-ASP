# #2 — Max-entropy seeds + decoherent coverage

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/2 · Milestone: M1 · Branch: `claude/mdc-conversion-features-gu3yzk`
Parent work item: [01-m0-public-blaster.md](01-m0-public-blaster.md) (shared owned files, test files, debug hook).

## Status

**Implemented on branch `claude/mdc-conversion-features-gu3yzk`** (static + e2e green, see *Acceptance tests*).
Before this branch the phone had a per-device seed persisted in `localStorage` and a `mulberry32` PRNG, but the seed
was `Math.random()`-derived, there was no minimum hop delta, no start stagger, no *Reseed* control, and the seed
source was invisible. This spec adds an entropy-mixed seed (`entropySeed()`), a minimum hop delta in `pickFreq`, a
start stagger, a *Reseed* button, and a `seedSource` indicator — all additive, all inside
`// ══ max-entropy seeds (#2) ══` plus three one-line edits listed below.

## Goal

Three phones opened on the same URL at the same second must **not** produce correlated hop sequences, and consecutive
hops on one phone must not land on (nearly) the same carrier. Seeds are mixed from several independent sources so that
even identical devices with identical clocks diverge; hop selection enforces a spectral distance; the first hop is
staggered so fleet phones do not all switch on the same audio-clock tick. Every seed is visible and re-rollable from
the UI, persisted, and reported in telemetry (`seed`, already on the wire).

## Prior art

- **Here:** `mulberry32` + per-device `localStorage` seed already in `public/index.html` (kept; only the seed *source*
  changes). Backend `seedAction: keep | reseed` in `docs/api-contract.md` / `clamps.py` (unchanged semantics).
- **Owner's Mac clone:** may carry UI tweaks around the seed row; the block is self-contained and the seed-init edit is
  four lines to minimise conflict.
- **OSS reused (not vendored — a few lines each, dependency-free rule):** bryc's `xmur3` string hash and the
  "hash a string to seed mulberry32" pattern (PRNGs.md), FNV-1a 32-bit (IETF draft parameters), Web Crypto
  `getRandomValues`. Considered and rejected: `sfc32` (issue #2 mentions it — no benefit over the existing
  `mulberry32` for this use, and a second PRNG is forbidden by the static test), `crypto.randomUUID()` (secure
  context only; `getRandomValues` works on `http://127.0.0.1` for the e2e), UA-string mixing (PII rule).

## Shipped on `main`

**Implemented on this branch** (`public/index.html` line numbers after the change):

| What | Where |
|------|-------|
| `let deviceId="", seed=0, seedSource="entropy"`; stored seed used only if it parses to an integer > 0, else `entropySeed()` + persist | `public/index.html:503-519` |
| `pickFreq` with `MIN_HOP_DELTA_HZ()` guard, ≤ 8 retries, skipped when band < 2·Δ | `public/index.html:554-561` |
| `start()`: `nextHopAt = ctx.currentTime + 0.05 + rand() * 0.5` | `public/index.html:847` |
| `// ══ max-entropy seeds (#2) ══`: `xmur3` (`:1423`), `fnv1a32` (`:1435`), `entropySeed` (`:1440`), `MIN_HOP_DELTA_HZ` (`:1453`, hoisted `function`), `reseed(reason)` (`:1454`), `reseedBtn` click → `reseed("ui")` (`:1462-1463`) | `public/index.html:1421-1463` |
| Remote `seedAction: "reseed"` → `reseed("patch")` (4 lines → 1) | `public/index.html:1583` |
| Systems check `Hop RNG` row: `per-device seed <seed> (<seedSource>) — min Δ <n> Hz — incoherent` | `public/index.html:1717` |
| `Reseed` button markup (`id="reseedBtn"`) in the Monitor tapbar | `public/index.html:375` |
| `window.__hop.getState()` exposes `seed`, `seedSource` (spec 01) | `public/index.html:1470` |
| `Math.floor(Math.random() * 1e9)` — **0 occurrences** remain | static test `test_entropy_seed` |

Baseline verified by reading `public/index.html` (`origin/main` @ `0625e91`, before this branch; lines of that revision):

| What | Where |
|------|-------|
| `deviceId` + `seed` init from `localStorage("hop.deviceId" / "hop.seed")`, fallback `Math.random()*1e9+1` | `public/index.html:494-507` |
| `mulberry32(a)` PRNG, `rng = mulberry32(seed >>> 0)`, `rand = () => rng()` | `public/index.html:523-525` |
| `bandLow()/bandHigh()` (Nyquist-ceiling aware), `dwellLo()/dwellHi()` | `public/index.html:537-540` |
| `pickFreq = () => bandLow() + rand()*(bandHigh()-bandLow())` — **uniform, no minimum delta** | `public/index.html:542` |
| `pickDwell` independent per hop | `public/index.html:543` |
| `scheduleHop()` — sets `lastTarget = f` after each pushed hop | `public/index.html:550-568` (`:565`) |
| `schedulePulse()` / `scheduleShriek()` also update `lastTarget` | `public/index.html:575-577`, `:604` |
| `schedule()` dispatcher | `public/index.html:609-614` |
| `setAlgo()` reschedule idiom (`pending.length = 0; nextHopAt = ctx.currentTime + 0.05; schedule()`) | `public/index.html:636-644` |
| `start()` — `lastTarget = pickFreq()`, first hop at `ctx.currentTime + 0.05` (**no stagger**) | `public/index.html:814-835` (`:820`, `:827`) |
| Remote `seedAction: "reseed"` → new `Math.random` seed, `rng` rebuilt, persisted, logged (**no reschedule**) | `public/index.html:1409-1414` |
| Monitor grid shows `seed` (`telSeed`) | `public/index.html:359`, `:1317` |
| Systems check row `Hop RNG — per-device seed <seed> — incoherent` | `public/index.html:1548` |
| Public copy: "Schedules are incoherent per Safari tab (independent RNG)" | `public/README.txt`; `public/index.html:381` |
| Rule: hops incoherent per tab; never a shared/global seed | `.claude/rules/public-frontend.md:34` |

## Remaining scope

Block `// ══ max-entropy seeds (#2) ══` placed after the watchdog block (spec 03) in the telemetry section. Because
`pickFreq` (`:542`) and the seed init (`:494-507`) are above the block, the block **reassigns** behaviour without
editing those lines where possible; where a line must change, the change is the smallest possible and listed here.

1. **String hash + entropy seed** (pure functions, no state):
   - `function xmur3(str)` — the xmur3 string-hash from bryc's PRNGs.md (see Sources), verbatim: init
     `h = 1779033703 ^ str.length`; per char `h = Math.imul(h ^ str.charCodeAt(i), 3432918353); h = h << 13 | h >>> 19;`
     returns a closure whose each call does `h = Math.imul(h ^ h >>> 16, 2246822507); h = Math.imul(h ^ h >>> 13,
     3266489909); return (h ^= h >>> 16) >>> 0;`. Only the first output is used (bryc's documented way to seed
     `mulberry32`).
   - `function fnv1a32(str)` — FNV-1a 32-bit: `h = 0x811c9dc5; for each byte: h ^= c; h = Math.imul(h, 0x01000193);`
     returns `h >>> 0`.
   - `function entropySeed()`:
     ```js
     let cr = [0,0,0,0];
     try { const u = new Uint32Array(4); crypto.getRandomValues(u); cr = Array.from(u); }
     catch (_) { cr = cr.map(() => Math.floor(Math.random() * 4294967296)); }
     const parts = [
       cr.join(","), String(Date.now()), String(Math.floor(performance.now() * 1000)),
       String(fnv1a32(deviceId || "")),
       String((screen && screen.width) || 0) + "x" + String((screen && screen.height) || 0)
     ];
     const s = xmur3(parts.join("|"))();           // uint32
     return (s % 2147483646) + 1;                    // 1 … 2^31-2, always a positive integer
     ```
     No `navigator.userAgent`, no language, no URL — the seed inputs never include anything that could carry PII.
     `crypto.getRandomValues` is available in insecure contexts too (MDN), so the `catch` is only for very old engines.
2. **Seed source at boot:** the init at `:494-507` is minimally edited: the two `Math.floor(Math.random() * 1e9) + 1`
   expressions become `entropySeed()` and a new `let seedSource = ss ? "stored" : "entropy";` is set (`"entropy"` in
   the `catch` branch too). `entropySeed` is a hoisted function declaration, so the call from `:502` is legal even
   though the block is defined later; `deviceId` is already assigned at that point. `rng = mulberry32(seed >>> 0)` at
   `:524` is unchanged.
3. **`reseed(reason)`** (in the block):
   `seed = entropySeed(); seedSource = "entropy"; rng = mulberry32(seed >>> 0);
   try { localStorage.setItem("hop.seed", String(seed)); } catch (_) {}
   monLog("seed reseeded → " + seed, "reseed", { seed, reason }, "info");
   if (running && ctx && osc) { pending.length = 0; nextHopAt = ctx.currentTime + 0.05; schedule(); }
   updateTelUI();`
   - `#reseedBtn` click → `reseed("ui")`.
   - The remote path at `:1409-1414` is edited to call `reseed("patch")` (4 lines → 1), so remote and UI reseed
     share one implementation and the remote reseed now also reschedules.
4. **Minimum hop delta:** `function MIN_HOP_DELTA_HZ(){ return Math.max(200, 0.05 * (bandHigh() - bandLow())); }`
   — shipped as a hoisted function declaration rather than a `const` arrow because `pickFreq` is defined ~900 lines
   above the block and `schedule()` can run before the block executes (a `const` would be in its TDZ).
   `pickFreq` at `:542` is replaced by
   ```js
   const pickFreq = () => {
     const lo = bandLow(), hi = bandHigh(), d = MIN_HOP_DELTA_HZ();
     let f = lo + rand() * (hi - lo);
     for (let i = 0; i < 8 && Math.abs(f - lastTarget) < d && (hi - lo) > 2 * d; i++) f = lo + rand() * (hi - lo);
     return f;
   };
   ```
   Up to 8 retries; if the band is narrower than `2·d` the guard is skipped (a 300 Hz band cannot honour a 200 Hz
   delta without starving). The RNG stream is still fully determined by `seed` (retries consume `rand()`
   deterministically). `lastTarget` is the `let` at `:485`, updated by all three schedulers.
5. **Start stagger:** in `start()` the line `nextHopAt = ctx.currentTime + 0.05;` (`:827`) becomes
   `nextHopAt = ctx.currentTime + 0.05 + rand() * 0.5;` — first hop delayed by a seed-determined 0–500 ms so three
   phones tapped together do not switch carriers on the same tick. `pickDwell` (`:543`) already gives independent dwells.
6. **UI:** `updateTelUI()` continues to write `telSeed`; the systems-check row at `:1548` becomes
   `row("Hop RNG", "ok", "per-device seed " + seed + " (" + seedSource + ") — min Δ " + Math.round(MIN_HOP_DELTA_HZ()) + " Hz — incoherent")`.
7. **Debug hook** (spec 01) exposes `seed` and `seedSource` via `window.__hop.getState()`.

## Wire fields

None new. `seed` (number) is already emitted at `public/index.html:1338` and documented in `docs/api-contract.md`
(sample payload `"seed": 42`). `seedAction: "reseed"` in patches (`api-contract.md` patch table) keeps its meaning and
now also reschedules. `seedSource` is **not** on the wire (UI/debug only).

## Clamps / safety

- No clamp constants change (`VOL_PATCH_MAX = 12`, band abs limits, `clampPatch()` untouched). `pickFreq` output is
  always within `[bandLow(), bandHigh()]`, which are already Nyquist-ceiling clamped (`:536-538`).
- **Hold / Manual:** a remote `seedAction: "reseed"` still never reaches `reseed()` when `holdManual` is true because
  `applyPatch` returns at `:1391` first. UI reseed is a local human action and is allowed during Hold.
- **No shared seed:** `entropySeed()` mixes CSPRNG output per call; two phones with identical `deviceId` fallback
  strings, identical screens and identical `Date.now()` still diverge on `getRandomValues`. The rule at
  `public-frontend.md:34` holds.
- Seeds are `1 … 2^31-2` (positive, safe integer, JSON-safe, `>>> 0`-stable).
- `mulberry32` period ~2^32; a reseed via UI/patch restarts the stream — acceptable for hours-long sessions.
- PII: seed inputs are CSPRNG, clocks, `fnv1a32(deviceId)` (a random local id) and screen size — no UA, no locale, no
  URL, no geolocation. The log record for reseed carries `{seed, reason}` only. (Review round: every `monLog`
  message is URL-query-scrubbed before storage — spec 01 §Clamps — so no reseed path can leak a `?patch=` value.)
- **Reseed = reschedule from now** with the *current* sliders: the watchdog's committed dwell (spec 03) is reset by
  the first hop of the fresh schedule; the e2e uses this to move from a 60 s to a 1 s committed dwell.

## Acceptance tests

**Result on this branch (2026-09-08 UTC):** static tests 1-7 are `test_entropy_seed`, `test_min_hop_delta_and_stagger`,
`test_reseed` in `tests/test_public_html.py` (`44 passed`, exit 0). Browser tests 8-12 are covered by the e2e tests
`seed is a positive entropy-mixed integer, persisted, reseedable` and `two independent contexts get different seeds`
(`bash tests/e2e/run.sh` → `9 passed`, exit 0 after the review round; static `48 passed`).

Static (`tests/test_public_html.py`, in addition to spec 01's checks):

1. `function entropySeed(` present exactly once; `crypto.getRandomValues(` present; `new Uint32Array(4)` present;
   `function xmur3(` and `function fnv1a32(` present; `0x811c9dc5` and `0x01000193` (FNV constants) present;
   `3432918353` (xmur3 constant) present.
2. `MIN_HOP_DELTA_HZ` present with the literal `Math.max(200, 0.05 * (bandHigh() - bandLow()))`.
3. `rand() * 0.5` present inside `start()` (text between `async function start(){` and the next `\n  }\n`).
4. `function reseed(` present; `seedSource` present; both `"stored"` and `"entropy"` literals present.
5. Exactly **one** occurrence of `Math.floor(Math.random() * 1e9)` remains at most (target: 0) — assert `<= 0`,
   i.e. the seed no longer derives from `Math.random`.
6. `entropySeed` inputs do not include PII: the `entropySeed` function body does not contain `userAgent`,
   `language`, `location.`, `geolocation`.
7. `mulberry32` definition still present exactly once (no second PRNG).

Browser (`tests/e2e/public_smoke.spec.mjs`, via `bash tests/e2e/run.sh`):

8. Fresh context: `getState().seedSource === "entropy"`, `Number.isInteger(seed) && seed > 0 && seed < 2**31`.
9. `page.reload()` in the same context: `seedSource === "stored"` and `seed` unchanged (localStorage persistence).
10. `click('#reseedBtn')`: `seed` changes, `localStorage["hop.seed"] === String(seed)`, `seedSource === "entropy"`,
    a log record `{event: "reseed", fields: {reason: "ui"}}` exists.
11. Two independent browser contexts (`browser.newContext()` × 2) loading the page produce **different** seeds.
12. Deterministic delta check via `page.evaluate`: with `#fMin=17000`, `#fMax=23000` (defaults),
    `MIN_HOP_DELTA_HZ` is not exported, so the test asserts indirectly: call `window.__hop.telemetryPayload()` twice
    around a reseed and confirm `fMin/fMax` unchanged (pickFreq stays in band). The Δ property itself is covered by
    the static regex (test 2) — a numeric assertion needs `__hop.pickFreq`, deliberately **not** exposed to keep the
    hook read-only.

## CI gate

- `tests` job runs `tests/test_public_html.py` (blocking). `static_gates` unchanged.
- Optional `e2e` job as in spec 01 (`@playwright/test` **1.56.1**, `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`
  locally; `npx playwright install --with-deps chromium` in CI only).
- No backend gate change: `seedAction` semantics unchanged for `clamps.validate_patch`.

## Risks / HW limits

- **Bluetooth latency jitter (tens to hundreds of ms)** already makes hop timing soft; the 0–500 ms stagger is of the
  same order and only guarantees decorrelation at the scheduler, not at the loudspeaker.
- **Minimum delta vs. narrow bands:** at 17–23 kHz `d = 300 Hz`; an operator narrowing to a 400 Hz band disables the
  guard (documented) rather than starving the scheduler.
- **`performance.now()` resolution** is coarsened on iOS Safari (≥ 1 ms, sometimes 100 µs quantised); it is only one
  of five mixed inputs.
- **Retry consumption of `rand()`** changes the sequence relative to a pre-#2 phone with the same seed. Seeds are not
  meant to be reproducible across app versions; telemetry `seed` remains a session identifier only.
- `screen.width/height` are identical across the two iPhone 16s — expected; entropy comes from CSPRNG.

## Sources

- Firecrawl developer search — https://github.com/cprosche/mulberry32 (README: Mulberry32 function form used at
  `public/index.html:523`, credits bryc's PRNG notes and the "seed from a string hash" pattern; period ≈ 2^32).
- bryc, *Pseudorandom number generators in JavaScript* — https://github.com/bryc/code/blob/master/jshash/PRNGs.md
  (xmur3 string hash with constant `3432918353`, mulberry32) — reached via the README above.
- Context7 `/mdn/content` — `Crypto.getRandomValues()` fills typed arrays (`Uint32Array` example) and is the only
  `Crypto` member usable from an insecure context.
- FNV-1a 32-bit parameters (offset basis `0x811c9dc5`, prime `0x01000193`): Fowler–Noll–Vo hash, IETF draft
  https://datatracker.ietf.org/doc/draft-eastlake-fnv/ (parameters table).
- GitHub issue #2 (read via the GitHub connector on 2026-09-08): "crypto-mixed seed (getRandomValues, UUID, time,
  localStorage device id, light UA/screen mix) → explicit PRNG (sfc32/mulberry32). Min frequency delta between hops,
  independent dwells, start stagger. Seed/device id UI + Reseed." — UA mixing intentionally **dropped** (PII rule).
- Repo: `CLAUDE.md`, `.claude/rules/public-frontend.md:34`, `docs/api-contract.md` (`seed`, `seedAction`),
  `public/index.html` (file:line cites above).
