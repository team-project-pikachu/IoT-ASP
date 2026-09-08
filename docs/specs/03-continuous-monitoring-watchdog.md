# #3 — Continuous polling & monitoring (all 3 phones on) — watchdog

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/3 · Milestone: M2 · Branch: `claude/mdc-conversion-features-gu3yzk`
Parent work item: [01-m0-public-blaster.md](01-m0-public-blaster.md) (shared owned files; structured log and
telemetry keys defined there).

## Status

**Spec — implementing in this branch.** The app keeps the Web Audio graph alive with an audio-clock scheduler, but
nothing recovers when iOS suspends/interrupts the `AudioContext` (phone call, Siri, route change, Control Center) or
when the scheduler stalls; the Monitor panel shows `ctx` state but no hop age or recovery counters. This spec adds a
1 s **watchdog** (`// ══ watchdog (#3) ══`): auto-resume of a non-running context, hop-age tracking, a stalled-scheduler
reschedule, three Monitor cells, and the `lastHopAgeMs` / `ctxResumes` / `watchdogTrips` heartbeat counters.

## Goal

While *Signal on* is active on all three phones, each phone independently (a) notices a non-`running` `AudioContext`
and resumes it, (b) notices a scheduler that has not produced a hop for longer than `dwellHi()·1.5 + 1 s` and
reschedules from *now*, (c) counts both recoveries, shows them in the Monitor grid and in the heartbeat, and
(d) writes a structured log record for every trip so the fleet log (#22) can aggregate stalls per node/night.

## Shipped on `main`

Verified by reading `public/index.html` (`origin/main` @ `0625e91`; exact lines):

| What | Where |
|------|-------|
| Audio-clock scheduler with `LOOKAHEAD = 0.25 s`, `TICK_MS = 40` | `public/index.html:532` |
| `pending[]` queue of scheduled hops (`{t, f, d, kind}`) filled by `scheduleHop/Pulse/Shriek` | `public/index.html:526`, `:564`, `:585`, `:603` |
| `schedule()` refills against `ctx.currentTime + LOOKAHEAD` | `public/index.html:609-614`, loops at `:552`, `:574`, `:593` |
| Reschedule-from-now idiom (`pending.length = 0; nextHopAt = ctx.currentTime + 0.05; schedule()`) | `public/index.html:636-644`, `:1416-1420` |
| `unlockAudio()` resumes a `suspended` context **only on gesture paths** | `public/index.html:779-782` |
| `ensureContext()` — 48 kHz, `latencyHint: "playback"` | `public/index.html:784-812` |
| `start()` / `stop()` set `running` | `public/index.html:814-835`, `:837-851` |
| `frame()` shifts due hops from `pending`, updates `history`, `hopCount`, countdown | `public/index.html:1173-1186` |
| `frame()` writes `ctxStateLabel` (`"ctx " + ctx.state`) — display only, no recovery | `public/index.html:1197` |
| `dwellLo()/dwellHi()` from the dwell sliders | `public/index.html:539-540` |
| Monitor grid cells (no hop-age / resume / watchdog cells) | `public/index.html:357-367` |
| Heartbeat every 2 s, payload without health counters | `public/index.html:1332-1360`, `:1456` |
| Structured `monLog(msg, event, fields, level)` (added by spec 01, same branch) | spec 01 §A |

## Remaining scope

Block `// ══ watchdog (#3) ══` placed after the telemetry-enrichment block (spec 01) and before the seeds block
(spec 02).

1. **State:** `let lastHopAt = 0, ctxResumes = 0, watchdogTrips = 0, lastWatchdogAt = 0;`
2. **Hop-age tracking:** in `frame()` the loop body at `:1176-1183` gains one line after `const hop = pending.shift();`
   → `lastHopAt = performance.now();`. `start()` (`:826`) sets `lastHopAt = performance.now();` when `running = true`
   so the first check has a baseline; `stop()` leaves it as-is (age is only meaningful while `running`).
3. **`function lastHopAgeMs()`** → `running && lastHopAt > 0 ? Math.round(performance.now() - lastHopAt) : null`.
4. **`function stallLimitMs()`** → `dwellHi() * 1.5 * 1000 + 1000` (dwell sliders are seconds; the pulse/shriek
   schedulers hop far more often than `dwellHi`, so the limit is conservative for them too).
5. **Watchdog tick** — `setInterval(watchdogTick, 1000)`, registered next to the existing intervals (`:1456-1458`):
   ```js
   function watchdogTick(){
     const now = performance.now();
     if (!running || !ctx) return;
     if (ctx.state !== "running") {
       ctxResumes++;
       monLog("ctx " + ctx.state + " → resume()", "watchdog", { state: ctx.state, ctxResumes }, "warn");
       try { const p = ctx.resume(); if (p && p.catch) p.catch(() => {}); } catch (_) {}
       return;                              // hop age is not judged while the clock is stopped
     }
     const age = lastHopAgeMs();
     if (age != null && age > stallLimitMs() && osc) {
       watchdogTrips++;
       pending.length = 0;
       nextHopAt = ctx.currentTime + 0.05;
       try { osc.frequency.cancelScheduledValues(ctx.currentTime); if (toneGain) toneGain.gain.cancelScheduledValues(ctx.currentTime); } catch (_) {}
       schedule();
       lastHopAt = now;                     // avoid re-tripping every second on the same stall
       monLog("watchdog reschedule", "watchdog", { ageMs: age, limitMs: Math.round(stallLimitMs()), watchdogTrips, algo: algoWireName() }, "warn");
     }
     lastWatchdogAt = now;
     updateTelUI();
   }
   ```
   The `cancelScheduledValues` calls mirror `setAlgo()` (`:639-642`) so stale automation from the stalled window does
   not fight the fresh schedule. `ctx.resume()` returns a promise that may reject while the page is backgrounded — it is
   swallowed and retried on the next tick (that is what the counter measures). No gesture is required for `resume()`
   once the context was originally unlocked by a gesture (`unlockAudio`, `:779-782`); iOS may still keep it
   `interrupted`/`suspended` until foregrounded, in which case `ctxResumes` keeps growing — that growth is the
   signal for the fleet log.
6. **Monitor cells** appended inside `.mon-grid` (`:357-367`, after `telSudden`):
   `<div>hop age <b id="telHopAge">—</b></div>`, `<div>ctx resumes <b id="telResumes">0</b></div>`,
   `<div>watchdog <b id="telWatchdog">0</b></div>`. `updateTelUI()` is extended (inside the watchdog block via a
   wrapper is not possible for a `function` declaration, so three `if (el) el.textContent = …` lines are appended to
   `updateTelUI()` at `:1329`): `telHopAge` = `age == null ? "—" : age + " ms"`, `telResumes` = `ctxResumes`,
   `telWatchdog` = `watchdogTrips`.
7. **Telemetry** (spec 01 §B): `lastHopAgeMs: lastHopAgeMs()`, `ctxResumes`, `watchdogTrips`.
8. **Systems check** row appended after `Patch hold` (`:1550`):
   `row("Watchdog", watchdogTrips === 0 ? "ok" : "bad", "1 s tick · stall > " + Math.round(stallLimitMs()) + " ms · trips " + watchdogTrips + " · ctx resumes " + ctxResumes)`.

Not in scope (issue text, parked for M2 follow-ups): optional mic SNR row, osc/gain node health beyond the
`osc` null-check, a background `Worker` timer to survive iOS timer throttling (see Risks).

## Wire fields

Additive under `schemaVersion: 1`; rows already in `docs/api-contract.md:84` (working tree):

| Field | Type | Phone value | Notes |
|-------|------|-------------|-------|
| `lastHopAgeMs` | number \| null | ms since the last hop left `pending`; `null` when not running | health |
| `ctxResumes` | number | count of `ctx.resume()` attempts by the watchdog since page load | health |
| `watchdogTrips` | number | count of stalled-scheduler reschedules since page load | health |

Log records (`logTail` / `getLog()`): `event: "watchdog"`, `level: "warn"`, `fields` ⊂ `{state, ctxResumes, ageMs,
limitMs, watchdogTrips, algo}` — numbers and enum strings only. Backend (`fleet_log`) treats unknown keys additively.

## Clamps / safety

- No clamp constants change; the watchdog never touches `fMin/fMax/vol/pulseMs/shriekMs` — it only clears `pending`
  and calls the existing `schedule()`, which uses the current (already clamped) slider values.
- **Hold / Manual is orthogonal:** the watchdog is local liveness, not a remote patch; it runs during Hold. It never
  calls `applyPatch`/`pollPatch`.
- **No gain increase on recovery:** `schedule()` re-applies `level()` at most; `stop()` semantics unchanged. If
  `running` is false the tick returns immediately, so a stopped phone never re-emits.
- Re-trip hysteresis: `lastHopAt = now` after a trip guarantees at least `stallLimitMs()` between trips; with default
  dwell sliders that is ≥ 2.5 s (`dwellHi ≥ 1 s`).
- `ctx.resume()` rejections are swallowed (no unhandled-rejection noise in Playwright's `pageerror`).
- PII: none of the fields are free text; `algo` is the wire enum.
- C1: no Bluetooth API involvement; route recovery is the OS's job, the watchdog only revives the Web Audio clock.

## Acceptance tests

Static (`tests/test_public_html.py`, alongside spec 01/02 checks):

1. Banner `// ══ watchdog (#3) ══` present; `setInterval(watchdogTick, 1000)` present; `function watchdogTick(`
   present exactly once.
2. `ctx.state !== "running"` and `ctx.resume()` both present inside the `watchdogTick` body; `ctxResumes++` and
   `watchdogTrips++` present.
3. `dwellHi() * 1.5 * 1000 + 1000` literal present (`stallLimitMs`).
4. `lastHopAt = performance.now();` occurs at least twice (frame shift + start).
5. `"watchdog reschedule"` literal present; `"watchdog"` used as the `event` argument (`, "watchdog",` present).
6. Ids `telHopAge`, `telResumes`, `telWatchdog` present inside the `mon-grid` div (text between
   `<div class="mon-grid">` and the following `</div>\n    <`).
7. `telemetryPayload` body contains `lastHopAgeMs`, `ctxResumes`, `watchdogTrips` (spec 01 test 3 covers this).
8. `navigator.bluetooth` absent (unchanged invariant).

Browser (`tests/e2e/public_smoke.spec.mjs`):

9. Before any gesture: `p = __hop.telemetryPayload()` has `p.lastHopAgeMs === null`, `p.ctxResumes === 0`,
   `p.watchdogTrips === 0`; `#telResumes` and `#telWatchdog` text is `0`; `#telHopAge` text is `—`.
10. Click `#power` (Signal on) — Chromium headless is launched by Playwright with autoplay allowed for user gestures;
    after `page.waitForTimeout(1500)`: `__hop.getState().running === true`, `telemetryPayload().lastHopAgeMs` is a
    finite number `≥ 0`, and `audioContextState === "running"`. If the context reports `suspended` in headless
    (no audio device), the test instead asserts `ctxResumes >= 1` within 3 s — i.e. the watchdog is observably
    attempting recovery — and marks the case in the test name (`"watchdog resumes suspended ctx"`).
11. Stall injection: `page.evaluate(() => { /* pending is closure-private */ })` cannot clear `pending`, so the test
    lowers the dwell sliders to their minimum (`#dMin`, `#dMax` → dispatch `input`), waits `stallLimitMs + 2000` ms
    while the page is running, and asserts `watchdogTrips === 0` (**no false trips** on a healthy scheduler).
    A positive trip is asserted via the structured log after `page.evaluate(() => window.__hop.getState())` only
    when `audioContextState !== "running"` (headless without audio): then `getLog().some(r => r.event === "watchdog")`.
12. Click `#power` again (Signal off): `running === false`, `lastHopAgeMs === null`, counters unchanged.

Exit code and any headless-audio caveat are recorded in the implementation notes.

## CI gate

- `tests` job (pytest) — blocking, via `tests/test_public_html.py`.
- `static_gates` — unchanged.
- Optional `e2e` job (spec 01 CI gate) — the watchdog cases 9–12 run in the same Playwright spec; headless Chromium
  may lack an audio sink, so cases 10–11 are written to pass on either `running` or `suspended` outcomes as stated.

## Risks / HW limits

- **iOS Safari timer throttling:** background tabs / locked screen throttle `setInterval` to ≥ 1 s and may pause it;
  the watchdog can only act while the page is foreground. Keeping the screen on (Guided Access / auto-lock off) is an
  operator step in the fleet runbook; a `Worker`-based tick is a follow-up, not in M2.
- **`AudioContext` `interrupted` state (WebKit):** iOS reports `"interrupted"` during calls/Siri; `resume()` may
  reject until the interruption ends. `ctxResumes` counts every attempt, so a long interruption shows as a large
  count — expected and useful.
- **Bluetooth route change** (speaker off/on) re-routes at OS level; Web Audio keeps running. The watchdog cannot
  detect a silent speaker — the mic/loopback path (`Listen`) remains the only acoustic self-check.
- **`performance.now()` monotonic across sleep?** On iOS it pauses during suspension, so a stall spanning a
  background period may under-report age; the ctx-state branch catches the common case first.
- **Headless Chromium without audio hardware** may leave the context `suspended`; e2e assertions accommodate this.

## Sources

- Context7 `/mdn/content` — `AudioContext.resume()` returns a Promise; `BaseAudioContext.state` values
  `suspended | running | closed` (WebKit additionally exposes `interrupted`); `performance.now()` monotonic
  high-resolution timer. (Queried alongside the `Intl`/`crypto`/clipboard lookups recorded in spec 01.)
- Context7 `/microsoft/playwright` — `PLAYWRIGHT_BROWSERS_PATH` for test runs; pin `@playwright/test` **1.56.1**
  (matches pre-installed `chromium-1194`; see spec 01 Sources for the version/revision evidence).
- GitHub issue #3 (read via the GitHub connector on 2026-09-08): "keep Web Audio graph alive, hop scheduler ticking,
  continuous poll of AudioContext state (auto-resume), osc/gain health, last hop age, seed/device id, optional mic
  SNR. Monitor panel + watchdog if no hop for > max(dwellHi)*1.5."
- Repo: `docs/iphone-bluetooth.md` (BT latency makes hop timing soft), `docs/DESIGN_CONSTRAINTS.md` C1,
  `.claude/rules/public-frontend.md:33-35`, `docs/api-contract.md:84`, `public/index.html` (file:line cites above).
