# #3 — Continuous polling & monitoring (all 3 phones on) — watchdog

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/3 · Milestone: M2 · Branch: `claude/mdc-conversion-features-gu3yzk`
Parent work item: [01-m0-public-blaster.md](01-m0-public-blaster.md) (shared owned files; structured log and
telemetry keys defined there).

## Status

**Implemented on `main`** (watchdog via #29/#33) **+ fleet heartbeat polish** (`feat/3-fleet-heartbeat-monitor`).
Per-device 1 s watchdog, AudioContext auto-resume, Monitor hop/resume/trip cells, and additive telemetry counters
are acceptance-green. Residual M2 close: fleet pulse strip (`#fleetHealth`) flags STALE peers when BroadcastChannel
heartbeats stop (> `FLEET_STALE_MS`), snaps carry watchdog fields, and Monitor shows live `#telSnr` / `micSnr`.
**Review round (2026-09-08):** stall limit uses the **committed schedule** (`committedDwellS`), not live `dwellHi()`.

## Goal

While *Signal on* is active on all three phones, each phone independently (a) notices a non-`running` `AudioContext`
and resumes it, (b) notices a scheduler that has not delivered the hop it **committed to** — either the committed
next hop is > 1 s behind the audio clock (`hopOverdue`) or no hop arrived for `committedDwell·1.5 + 1 s` on the wall
clock while the context claims `running` (`clockStalled`) — and reschedules from *now*, (c) counts both recoveries,
shows them in the Monitor grid and in the heartbeat, and
(d) writes a structured log record for every trip so the fleet log (#22) can aggregate stalls per node/night.

## Prior art

- **Here:** the audio-clock scheduler (`pending[]`, `schedule()`, `LOOKAHEAD`/`TICK_MS`), the reschedule-from-now idiom
  in `setAlgo()`/`applyPatch()`, and `unlockAudio()`'s gesture-path `resume()` — the watchdog reuses all three instead of
  adding a second scheduler. `ctxStateLabel` already displayed `ctx.state` (display only).
- **Owner's Mac clone:** unknown; the block only adds one line to `frame()` and one to `start()`.
- **Backend:** `fleet_log` (#22) already treats unknown telemetry keys additively, so `lastHopAgeMs`/`ctxResumes`/
  `watchdogTrips` need no backend change.
- **OSS / platform:** Web Audio `AudioContext.resume()` promise + `state` (MDN); the common "keep the AudioContext
  alive on iOS" pattern is a periodic `state !== "running" → resume()` poll — adopted as-is. A `Worker`-based timer to
  dodge background throttling is documented as a follow-up, not adopted (M2 scope, no evidence it survives iOS
  lock-screen suspension either).

## Shipped on `main`

**Implemented on this branch** (`public/index.html` line numbers after the change):

| What | Where |
|------|-------|
| Monitor cells `telHopAge` / `telResumes` / `telWatchdog` after `telSudden` (`<!-- ══ watchdog cells (#3) ══ -->`) | `public/index.html:367-370` |
| `start()`: `lastHopAt = performance.now(); lastHopDwellS = 0` baseline (no dwell committed yet) | `public/index.html:846` |
| `frame()`: hop delivery delegated to `shiftDueHops()` (shared with the watchdog) | `public/index.html:1196` |
| `// ══ watchdog (#3) ══`: `var lastHopAt, lastHopDwellS, ctxResumes, watchdogTrips, lastWatchdogAt` (`:1395`), `STALL_GRACE_S = 1.0` (`:1396`), `lastHopAgeMs()`, `committedDwellS()` (`:1400`), `stallLimitMs()` (`:1401`), `nextHopDueAt()` / `nextHopOverdueMs()` (`:1402-1403`), `shiftDueHops()` (`:1406-1419`, records `lastHopAt` + `lastHopDwellS = hop.d`), `watchdogTick()` (`:1421-1452`), `setInterval(watchdogTick, 1000)` (`:1453`) | `public/index.html:1386-1453` |
| `updateTelUI()` fills the three cells (`—` when not running) | `public/index.html:1523-1527` |
| `telemetryPayload()`: `lastHopAgeMs`, `ctxResumes`, `watchdogTrips` | `public/index.html:1563-1565` |
| Debug hook `getWatchdog()` (numbers only: `lastHopAgeMs`, `nextHopOverdueMs`, `stallLimitMs`, `committedDwellS`, `ctxResumes`, `watchdogTrips`) | `public/index.html:1505` |
| Systems check `Watchdog` row after `Patch hold` | `public/index.html:1755` |
| Log records `event: "watchdog"`, `level: "warn"`, `fields.reason ∈ {hopOverdue, clockStalled}` via structured `monLog` (spec 01) | `public/index.html:1426`, `:1449` |

Shipped deviations from the text below: counters are `var` (boot order — `setAlgo()` from `localStorage` (`:1317`) calls
`updateTelUI()` before the block runs; a `let` would throw in its TDZ), and `watchdogTick()` also calls `updateTelUI()`
in the resume branch so `telResumes` updates on the same tick.

**Shipped stall judgement (supersedes items 3-5 of *Remaining scope*, which record the original brief):**

```js
var lastHopAt = 0, lastHopDwellS = 0, ctxResumes = 0, watchdogTrips = 0, lastWatchdogAt = 0;
const STALL_GRACE_S = 1.0;
function committedDwellS(){ return lastHopDwellS > 0 ? lastHopDwellS : dwellHi(); }   // hop.d of the hop in flight
function stallLimitMs(){ return committedDwellS() * 1.5 * 1000 + 1000; }
function nextHopDueAt(){ return pending.length ? pending[0].t : nextHopAt; }
function nextHopOverdueMs(){ return running && ctx ? Math.round((ctx.currentTime - nextHopDueAt()) * 1000) : null; }
function shiftDueHops(){ /* frame()'s old while-loop + `lastHopDwellS = hop.d` */ }
function watchdogTick(){
  … resume branch unchanged …
  if (osc) shiftDueHops();                     // a paused rAF loop (hidden tab) is not a dead scheduler
  const age = lastHopAgeMs(), overdue = nextHopOverdueMs();
  const reason = overdue > STALL_GRACE_S * 1000 ? "hopOverdue" : age > stallLimitMs() ? "clockStalled" : null;
  if (reason && osc) { …trip as before…; lastHopDwellS = 0; monLog("watchdog reschedule", "watchdog", { reason, ageMs, overdueMs, limitMs, watchdogTrips, algo }, "warn"); }
}
```

Why two conditions: `hopOverdue` catches a scheduler that stopped refilling/draining while the audio clock runs
(`nextHopAt` falls behind `ctx.currentTime`); `clockStalled` catches an audio clock that froze while `state` still says
`running` (iOS route change / interruption) — there the committed hop never becomes due, so only the wall clock can
tell. Neither reads the live dwell sliders: lowering `dMin`/`dMax` after a 60 s dwell was committed keeps
`stallLimitMs() = 91 000` until that hop lands (e2e test 11). `shiftDueHops()` is the single place that records the
commitment, so `frame()` and the watchdog can never disagree on "the hop in flight".

Baseline verified by reading `public/index.html` (`origin/main` @ `0625e91`, before this branch; lines of that revision):

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

Monitor SNR row (`#telSnr` / `micSnr`) and fleet 3-phone heartbeat view shipped with the M2 close PR.
Still parked follow-ups: osc/gain node health beyond the `osc` null-check; a background `Worker` timer to survive
iOS timer throttling (see Risks); cross-origin / native multi-phone heartbeats without same-origin tabs (#10).

## Wire fields

Additive under `schemaVersion: 1`; rows already in `docs/api-contract.md:84` (working tree):

| Field | Type | Phone value | Notes |
|-------|------|-------------|-------|
| `lastHopAgeMs` | number \| null | ms since the last hop left `pending`; `null` when not running | health |
| `ctxResumes` | number | count of `ctx.resume()` attempts by the watchdog since page load | health |
| `watchdogTrips` | number | count of stalled-scheduler reschedules since page load | health |
| `micSnr` | number \| null | US-band peak−floor SNR (dB); null until mic/loop decode | monitor |

Log records (`logTail` / `getLog()`): `event: "watchdog"`, `level: "warn"`, `fields` ⊂ `{state, ctxResumes, reason,
ageMs, overdueMs, limitMs, watchdogTrips, algo}` — numbers and enum strings only (`reason ∈ {hopOverdue,
clockStalled}`). Backend (`fleet_log`) treats unknown keys additively.

## Clamps / safety

- No clamp constants change; the watchdog never touches `fMin/fMax/vol/pulseMs/shriekMs` — it only clears `pending`
  and calls the existing `schedule()`, which uses the current (already clamped) slider values.
- **Hold / Manual is orthogonal:** the watchdog is local liveness, not a remote patch; it runs during Hold. It never
  calls `applyPatch`/`pollPatch`.
- **No gain increase on recovery:** `schedule()` re-applies `level()` at most; `stop()` semantics unchanged. If
  `running` is false the tick returns immediately, so a stopped phone never re-emits.
- Re-trip hysteresis: `lastHopAt = now` after a trip guarantees at least `stallLimitMs()` between trips; with default
  dwell sliders that is ≥ 2.5 s (`dwellHi ≥ 1 s`).
- **No false trips from slider edits (review finding):** the limit is derived from the committed `hop.d`, not from
  `dwellHi()`; `syncDwell()` still never reschedules, so a lowered slider only takes effect at the next hop. The only
  ways to shorten a committed dwell remain the explicit reschedules (`setAlgo`, `applyPatch`, `reseed`).
- **Hidden tab:** `rAF` pauses `frame()`, but the watchdog drains `pending` itself, so an undrained queue is not
  reported as `hopOverdue`; the 1 s-throttled `schedule()` keeps `nextHopAt` within `LOOKAHEAD + 1 s` of the clock.
- `ctx.resume()` rejections are swallowed (no unhandled-rejection noise in Playwright's `pageerror`).
- PII: none of the fields are free text; `algo` is the wire enum.
- C1: no Bluetooth API involvement; route recovery is the OS's job, the watchdog only revives the Web Audio clock.

## Acceptance tests

**Result on this branch (2026-09-08 UTC):** static tests 1-8 are `test_watchdog`, `test_watchdog_cells_in_mon_grid`,
`test_telemetry_payload_tokens`, `test_no_web_bluetooth` in `tests/test_public_html.py` (`44 passed`, exit 0).
Browser tests 9-12 are the e2e tests `telemetryPayload carries schemaVersion 1 + #22 / #3 fields` (9) and
`watchdog: no false trips on a healthy scheduler (Hold + sudden-auto off), trips on a real stall` (10-12);
`bash tests/e2e/run.sh` → `9 passed (14.7s)`, exit 0 after the review round (static: `48 passed`, incl.
`test_watchdog_stall_uses_committed_schedule`). **Headless-audio caveat observed:** Playwright's Chromium 141
(`chromium-1194`) reported `audioContextState: "running"` 1.5 s after *Signal on*, so the "running" branch ran:
committed dwell ≈ 60 s survived `dMin = dMax = 1 s` for 4.5 s with `watchdogTrips 0` and no `watchdog` log record;
after *Reseed* (committed dwell ≤ 1 s, limit ≤ 2 500 ms) a frozen audio clock produced a trip with
`fields.reason === "clockStalled"` within 8 s. The `suspended` branch (`ctxResumes ≥ 1` within 3 s) remains for sinks
without audio.

Static (`tests/test_public_html.py`, alongside spec 01/02 checks):

1. Banner `// ══ watchdog (#3) ══` present; `setInterval(watchdogTick, 1000)` present; `function watchdogTick(`
   present exactly once.
2. `ctx.state !== "running"` and `ctx.resume()` both present inside the `watchdogTick` body; `ctxResumes++` and
   `watchdogTrips++` present.
3. `committedDwellS() * 1.5 * 1000 + 1000` literal present (`stallLimitMs`); `stallLimitMs` body contains no
   `dwellHi()` (review regression `test_watchdog_stall_uses_committed_schedule`, which also pins `shiftDueHops()`,
   `lastHopDwellS = hop.d;` once, `STALL_GRACE_S = 1.0`, the two `reason` enums and the `start()` reset).
4. `lastHopAt = performance.now();` occurs at least twice (frame shift + start).
5. `"watchdog reschedule"` literal present; `"watchdog"` used as the `event` argument (`, "watchdog",` present).
6. Ids `telHopAge`, `telResumes`, `telWatchdog` present inside the `mon-grid` div (text between
   `<div class="mon-grid">` and the following `</div>\n    <`).
7. `telemetryPayload` body contains `lastHopAgeMs`, `ctxResumes`, `watchdogTrips` (spec 01 test 3 covers this).
8. `navigator.bluetooth` absent (unchanged invariant).

Browser (`tests/e2e/public_smoke.spec.mjs`):

9. Before any gesture: `p = __hop.telemetryPayload()` has `p.lastHopAgeMs === null`, `p.ctxResumes === 0`,
   `p.watchdogTrips === 0`; `#telResumes` and `#telWatchdog` text is `0`; `#telHopAge` text is `—`.
10. Isolation first (review finding 2): click `#holdPatchBtn` (no remote patch can reschedule) and `#suddenOff`
    (no sudden-auto rotation), set `#dMin = #dMax = 60` (both values set before either `input` fires — `syncDwell`
    clamps `dMin` to `dMax` otherwise), then click `#power` (Signal on). After `page.waitForTimeout(1500)`:
    `getState().running === true`, `algo === "hop"`, `telemetryPayload().lastHopAgeMs` finite `≥ 0`,
    `getWatchdog().committedDwellS ≈ 60`, `stallLimitMs === 91000`. If the context reports `suspended` in headless
    (no audio device), the test instead asserts `ctxResumes >= 1` within 3 s and a `watchdog` log record, then ends.
11. **No false trips:** set `#dMin = #dMax = 1`, wait `1·1.5·1000 + 1000 + 2000` ms → `committedDwellS` still ≈ 60,
    `watchdogTrips === 0`, `nextHopOverdueMs < 0`, no `event === "watchdog"` record, `#telWatchdog` text `0`, `algo`
    unchanged. **Real stall:** click `#reseedBtn` (reschedule under the 1 s dwell) and wait until
    `getWatchdog().committedDwellS ∈ (0, 1]` (`stallLimitMs ≤ 2500`); then set `window.__freezeAudioClock = true`
    (an `addInitScript` wraps the `BaseAudioContext.prototype.currentTime` getter so the clock the page reads holds
    still while `state` stays `running` — the app is untouched) and wait ≤ 8 s for `watchdogTrips >= 1`. The trip
    record has `msg === "watchdog reschedule"`, `level === "warn"`, `fields.reason === "clockStalled"`,
    `fields.limitMs ≤ 2500`, `fields.ageMs > fields.limitMs`, `fields.algo === "hop"`; `ctxResumes === 0`;
    `#telWatchdog` is no longer `0`.
12. Unfreeze, click `#power` again (Signal off): `running === false`, `lastHopAgeMs === null`, `watchdogTrips`
    kept (≥ 1), no `pageerror`.

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
