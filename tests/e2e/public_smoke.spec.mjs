// Playwright smoke for public/index.html — drives the real single-file app in headless Chromium.
// Assertions follow docs/specs/01-m0-public-blaster.md (13-19), 02-max-entropy-seeds.md (8-12),
// 03-continuous-monitoring-watchdog.md (9-12). Uses the read-only window.__hop debug hook.
import { test, expect } from "@playwright/test";

const PORT = process.env.E2E_PORT || "8765";
test.use({ baseURL: `http://127.0.0.1:${PORT}` });

// `fleet` is a per-record snapshot for Copy fleet_log JSONL (#22); keep exact key order.
const LOG_KEYS = ["seq", "ts", "level", "event", "msg", "fields", "fleet"];

async function openPage(page) {
  const errors = [];
  page.on("pageerror", e => errors.push(String(e)));
  const resp = await page.goto("/");
  expect(resp.status()).toBe(200);
  await page.waitForFunction(() => !!window.__hop);
  return errors;
}

const state = page => page.evaluate(() => window.__hop.getState());
const payload = page => page.evaluate(() => window.__hop.telemetryPayload());
const log = page => page.evaluate(() => window.__hop.getLog());
const watchdog = page => page.evaluate(() => window.__hop.getWatchdog());
// Both values are set before either `input` fires: syncDwell() clamps dMin back to dMax when dMin alone is raised.
const setDwell = (page, s) => page.evaluate(v => {
  const els = ["dMin", "dMax"].map(id => document.getElementById(id));
  for (const el of els) el.value = String(v);
  for (const el of els) el.dispatchEvent(new Event("input"));
}, s);
// Stall injection: freeze BaseAudioContext.currentTime on demand (window.__freezeAudioClock = true). The app is
// untouched; only the audio clock the page reads is held, which is what an iOS route change / interruption looks
// like from JS ("running" state, clock not advancing). Must be installed before the page script runs.
const FREEZE_INIT = () => {
  const proto = window.BaseAudioContext && window.BaseAudioContext.prototype;
  const d = proto && Object.getOwnPropertyDescriptor(proto, "currentTime");
  if (!d || !d.get) return;
  let frozen = null;
  Object.defineProperty(proto, "currentTime", { configurable: true, get() {
    const t = d.get.call(this);
    if (window.__freezeAudioClock) { if (frozen == null) frozen = t; return frozen; }
    frozen = null; return t;
  } });
};

test.describe("public blaster smoke", () => {
  test("loads, ids exist, no page errors", async ({ page }) => {
    const errors = await openPage(page);
    expect((await page.title()).length).toBeGreaterThan(0);
    for (const id of ["holdPatchBtn", "copyLogBtn", "reseedBtn", "telHopAge", "telResumes", "telWatchdog", "monLog", "power"]) {
      await expect(page.locator(`#${id}`)).toBeAttached();
    }
    await expect(page.locator("#holdPatchBtn")).toHaveText("Hold / Manual");
    expect(errors).toEqual([]);
  });

  test("Hold / Manual toggles holdManual", async ({ page }) => {
    const errors = await openPage(page);
    expect((await state(page)).holdManual).toBe(false);
    await page.click("#holdPatchBtn");
    expect((await state(page)).holdManual).toBe(true);
    await expect(page.locator("#holdPatchBtn")).toHaveAttribute("aria-pressed", "true");
    expect((await payload(page)).holdManual).toBe(true);
    await page.click("#holdPatchBtn");
    expect((await state(page)).holdManual).toBe(false);
    expect(errors).toEqual([]);
  });

  test("telemetryPayload carries schemaVersion 1 + #22 / #3 fields", async ({ page }) => {
    await openPage(page);
    const p = await payload(page);
    expect(p.schemaVersion).toBe(1);
    expect(["17-23k", "10-20"]).toContain(p.band);
    expect(p.band).toBe("17-23k");
    expect(typeof p.nightNY).toBe("boolean");
    expect(p.power).toBe("ac120");
    expect(p.lfArmed).toBe(false);
    expect(p.lfDriveCapable).toBe(false);
    expect(Array.isArray(p.logTail)).toBe(true);
    expect(p.logTail.length).toBeLessThanOrEqual(3);
    expect(Number.isInteger(p.logSeq)).toBe(true);
    expect(typeof p.holdManual).toBe("boolean");
    expect(p.deviceId).toMatch(/^dev-[a-z0-9]{8}$/);
    expect(p.ts).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
    // watchdog counters before any gesture
    expect(p.lastHopAgeMs).toBeNull();
    expect(p.ctxResumes).toBe(0);
    expect(p.watchdogTrips).toBe(0);
    await expect(page.locator("#telResumes")).toHaveText("0");
    await expect(page.locator("#telWatchdog")).toHaveText("0");
    await expect(page.locator("#telHopAge")).toHaveText("—");
    // no PII-ish keys on the wire
    for (const k of ["userAgent", "lat", "lon", "address"]) expect(p).not.toHaveProperty(k);
  });

  test("seed is a positive entropy-mixed integer, persisted, reseedable", async ({ page }) => {
    const errors = await openPage(page);
    const s0 = await state(page);
    expect(Number.isInteger(s0.seed) && s0.seed > 0 && s0.seed < 2 ** 31).toBe(true);
    expect(["stored", "entropy"]).toContain(s0.seedSource);
    expect(s0.seedSource).toBe("entropy");

    await page.reload();
    await page.waitForFunction(() => !!window.__hop);
    const s1 = await state(page);
    expect(s1.seedSource).toBe("stored");
    expect(s1.seed).toBe(s0.seed);

    await page.click("#reseedBtn");
    const s2 = await state(page);
    expect(s2.seed).not.toBe(s1.seed);
    expect(Number.isInteger(s2.seed) && s2.seed > 0).toBe(true);
    expect(s2.seedSource).toBe("entropy");
    expect(await page.evaluate(() => localStorage.getItem("hop.seed"))).toBe(String(s2.seed));
    const recs = await log(page);
    const r = recs.find(x => x.event === "reseed");
    expect(r).toBeTruthy();
    expect(r.fields.reason).toBe("ui");
    expect(r.fields.seed).toBe(s2.seed);
    // band unchanged across reseed
    const p = await payload(page);
    expect(p.fMin).toBe(17000);
    expect(p.fMax).toBe(21000);
    expect(errors).toEqual([]);
  });

  test("two independent contexts get different seeds", async ({ browser }) => {
    const a = await browser.newContext(), b = await browser.newContext();
    const pa = await a.newPage(), pb = await b.newPage();
    await openPage(pa); await openPage(pb);
    const sa = await state(pa), sb = await state(pb);
    expect(sa.seed).not.toBe(sb.seed);
    await a.close(); await b.close();
  });

  test("Copy log JSON does not throw; structured records well-formed", async ({ page }) => {
    const errors = await openPage(page);
    await page.click("#copyLogBtn");
    await page.waitForFunction(() => window.__hop.getLog().some(r => r.event === "ui"));
    const recs = await log(page);
    expect(recs.length).toBeGreaterThan(0);
    let prev = 0;
    for (const r of recs) {
      expect(Object.keys(r)).toEqual(LOG_KEYS);
      expect(r.seq).toBeGreaterThan(prev);
      prev = r.seq;
      expect(["debug", "info", "warn", "error"]).toContain(r.level);
    }
    expect(errors).toEqual([]);
  });

  test("watchdog: no false trips on a healthy scheduler (Hold + sudden-auto off), trips on a real stall", async ({ page }) => {
    await page.addInitScript(FREEZE_INIT);
    const errors = await openPage(page);
    // Remove the confounders (review finding 2): no remote patch (Hold / Manual) and no sudden-auto rotation, so
    // only the hop scheduler and the watchdog are running.
    await page.click("#holdPatchBtn");
    await page.click("#suddenOff");
    expect((await state(page)).holdManual).toBe(true);
    await setDwell(page, 60);
    await page.click("#power");
    await page.waitForTimeout(1500);
    const s = await state(page);
    expect(s.running).toBe(true);
    expect(s.algo).toBe("hop");
    let p = await payload(page);
    if (p.audioContextState !== "running") {
      // headless without an audio sink: the watchdog must be observably attempting recovery
      await page.waitForFunction(() => window.__hop.telemetryPayload().ctxResumes >= 1, null, { timeout: 3000 });
      expect((await log(page)).some(r => r.event === "watchdog")).toBe(true);
      await page.click("#power");
      expect((await payload(page)).lastHopAgeMs).toBeNull();
      expect(errors).toEqual([]);
      return;
    }
    // first hop delivered with a committed dwell of ~60 s
    expect(Number.isFinite(p.lastHopAgeMs) && p.lastHopAgeMs >= 0).toBe(true);
    let w = await watchdog(page);
    expect(w.committedDwellS).toBeCloseTo(60, 0);
    expect(w.stallLimitMs).toBe(Math.round(60 * 1.5 * 1000 + 1000));
    // review finding 1: lowering the sliders mid-dwell must NOT change the committed limit nor trip the watchdog
    await setDwell(page, 1);
    await page.waitForTimeout(1 * 1.5 * 1000 + 1000 + 2000);
    w = await watchdog(page);
    expect(w.committedDwellS).toBeCloseTo(60, 0);
    expect(w.watchdogTrips).toBe(0);
    expect(w.nextHopOverdueMs).toBeLessThan(0);
    expect((await payload(page)).watchdogTrips).toBe(0);
    expect((await log(page)).filter(r => r.event === "watchdog")).toEqual([]);
    await expect(page.locator("#telWatchdog")).toHaveText("0");
    expect(s.algo).toBe((await state(page)).algo);            // no patch applied while held
    // reschedule under the 1 s dwell (Reseed = reschedule from now) → committed dwell ≈ 1 s, limit 2.5 s
    await page.click("#reseedBtn");
    await page.waitForFunction(() => { const w = window.__hop.getWatchdog(); return w.committedDwellS > 0 && w.committedDwellS <= 1.0; }, null, { timeout: 5000 });
    w = await watchdog(page);
    expect(w.stallLimitMs).toBeLessThanOrEqual(2500);
    expect(w.watchdogTrips).toBe(0);
    // real stall: freeze the audio clock while the context still reports "running"
    await page.evaluate(() => { window.__freezeAudioClock = true; });
    await page.waitForFunction(() => window.__hop.getWatchdog().watchdogTrips >= 1, null, { timeout: 8000 });
    const trip = (await log(page)).find(r => r.event === "watchdog" && r.msg === "watchdog reschedule");
    expect(trip).toBeTruthy();
    expect(trip.level).toBe("warn");
    expect(trip.fields.reason).toBe("clockStalled");
    expect(trip.fields.limitMs).toBeLessThanOrEqual(2500);
    expect(trip.fields.ageMs).toBeGreaterThan(trip.fields.limitMs);
    expect(trip.fields.algo).toBe("hop");
    p = await payload(page);
    expect(p.watchdogTrips).toBeGreaterThanOrEqual(1);
    expect(p.ctxResumes).toBe(0);
    await expect(page.locator("#telWatchdog")).not.toHaveText("0");
    await page.evaluate(() => { window.__freezeAudioClock = false; });
    // Signal off resets the age; counters are kept
    await page.click("#power");
    expect((await state(page)).running).toBe(false);
    p = await payload(page);
    expect(p.lastHopAgeMs).toBeNull();
    expect(p.watchdogTrips).toBeGreaterThanOrEqual(1);
    expect(errors).toEqual([]);
  });

  test("?patch= query string never reaches the log ring buffer, logTail or Copy log JSON", async ({ page }) => {
    const errors = [];
    page.on("pageerror", e => errors.push(String(e)));
    const resp = await page.goto("/?patch=" + encodeURIComponent("/patch.json?X-Goog-Signature=SECRETSIG123&X-Goog-Expires=60"));
    expect(resp.status()).toBe(200);
    await page.waitForFunction(() => !!window.__hop);
    const recs = await log(page);
    expect(recs.length).toBeGreaterThan(0);
    const ready = recs.find(r => r.msg.startsWith("scientific tooling ready"));
    expect(ready).toBeTruthy();
    expect(ready.msg).toBe("scientific tooling ready · patch /patch.json?[redacted] · poll 3000ms (hot-apply)");
    expect(JSON.stringify(recs)).not.toContain("SECRETSIG123");
    expect(JSON.stringify(await payload(page))).not.toContain("SECRETSIG123");
    // the poll still targets the full URL (app behaviour unchanged) — only the log copy is scrubbed
    await expect(page.locator("#patchUrlLabel")).toHaveText("/patch.json?X-Goog-Signature=SECRETSIG123&X-Goog-Expires=60");
    await page.waitForTimeout(2500);                        // a beacon tick + a poll → more log lines
    expect(JSON.stringify(await log(page))).not.toContain("SECRETSIG123");
    expect(JSON.stringify((await payload(page)).logTail)).not.toContain("SECRETSIG123");
    expect(errors).toEqual([]);
  });

  test("bare relative ?patch= query is redacted in the log ring buffer", async ({ page }) => {
    const errors = [];
    page.on("pageerror", e => errors.push(String(e)));
    const resp = await page.goto("/?patch=" + encodeURIComponent("patch.json?token=SECRETREL456"));
    expect(resp.status()).toBe(200);
    await page.waitForFunction(() => !!window.__hop);
    const recs = await log(page);
    const ready = recs.find(r => r.msg.startsWith("scientific tooling ready"));
    expect(ready).toBeTruthy();
    expect(ready.msg).toContain("patch.json?[redacted]");
    expect(JSON.stringify(recs)).not.toContain("SECRETREL456");
    expect(JSON.stringify(await payload(page))).not.toContain("SECRETREL456");
    await expect(page.locator("#patchUrlLabel")).toHaveText("patch.json?token=SECRETREL456");
    expect(errors).toEqual([]);
  });


  test("two tabs exchange fleet heartbeats + simulate impulse (#11 #22 #44)", async ({ browser }) => {
    const context = await browser.newContext();
    const pageA = await context.newPage();
    const pageB = await context.newPage();
    const errors = [];
    pageA.on("pageerror", e => errors.push(String(e)));
    pageB.on("pageerror", e => errors.push(String(e)));
    await pageA.goto("/");
    await pageB.goto("/");
    await pageA.waitForFunction(() => !!window.__hop);
    await pageB.waitForFunction(() => !!window.__hop);
    const meta = await Promise.all([
      pageA.evaluate(() => ({ ...window.__hop.getState(), tabSeed: sessionStorage.getItem("hop.tabSeed") })),
      pageB.evaluate(() => ({ ...window.__hop.getState(), tabSeed: sessionStorage.getItem("hop.tabSeed") })),
    ]);
    // Shared telemetry deviceId; distinct per-tab instanceId + session seed for peer compare
    expect(meta[0].deviceId).toBeTruthy();
    expect(meta[0].instanceId).toBeTruthy();
    expect(meta[0].instanceId).not.toBe(meta[1].instanceId);
    expect(String(meta[0].seed)).not.toBe(String(meta[1].seed));
    await pageA.waitForFunction(() => {
      const t = document.getElementById("fleetSeedCompare")?.textContent || "";
      return /incoherent OK/.test(t) || /peers=/.test(t);
    }, null, { timeout: 8000 });
    await pageA.waitForFunction(() => {
      const h = document.getElementById("fleetHealth")?.textContent || "";
      return /Fleet pulse/.test(h) && /live/.test(h);
    }, null, { timeout: 5000 });
    const health = await pageA.locator("#fleetHealth").textContent();
    expect(health).toMatch(/2\/3 live|3\/3 live|all phones on/);
    await pageA.click("#simImpulseBtn");
    await pageA.waitForFunction(() => {
      const p = window.__hop.telemetryPayload();
      return (p.impulse === true || p.volBlast === true)
        && (p.alarmState === "triggered" || p.alarmState === "sustaining")
        && p.extremeActive === true;
    }, null, { timeout: 5000 });
    const p = await pageA.evaluate(() => window.__hop.telemetryPayload());
    expect(p.extremeActive).toBe(true);
    expect(["triggered", "sustaining"]).toContain(p.alarmState);
    // Hold restores volume path and cleared latch
    await pageA.click("#holdPatchBtn");
    await pageA.waitForFunction(() => window.__hop.getState().alarmState === "cleared", null, { timeout: 3000 });
    // Fleet JSONL rows preserve per-record fleet snapshots (ts/event), not only live telemetry
    const jsonl = await pageA.evaluate(async () => {
      const orig = navigator.clipboard?.writeText?.bind(navigator.clipboard);
      let captured = "";
      if (navigator.clipboard) {
        navigator.clipboard.writeText = async (t) => { captured = String(t || ""); };
      }
      document.getElementById("copyFleetLogBtn")?.click();
      await new Promise(r => setTimeout(r, 50));
      if (orig) navigator.clipboard.writeText = orig;
      return captured;
    });
    expect(jsonl.trim().length).toBeGreaterThan(0);
    const rows = jsonl.trim().split("\n").map(l => JSON.parse(l));
    expect(rows[0].kind).toBe("fleet_log");
    expect(rows[0].ts).toBeTruthy();
    expect(errors).toEqual([]);
    await context.close();
  });

  test("systems check escapes a reflected ?patch= value (no XSS)", async ({ page }) => {
    const errors = [];
    page.on("pageerror", e => errors.push(String(e)));
    const evil = 'x<img src=x onerror="window.__xss=1">';
    await page.goto("/?patch=" + encodeURIComponent(evil));
    await page.waitForFunction(() => !!window.__hop);
    await page.click("#sysBtn");
    await page.waitForFunction(() => /Patch hold/.test(document.getElementById("sysList").textContent), null, { timeout: 20000 });
    expect(await page.evaluate(() => window.__xss)).toBeUndefined();
    expect(await page.locator("#sysList img").count()).toBe(0);
    expect(await page.locator("#sysList").innerHTML()).not.toContain("<img");
    expect(await page.locator("#sysList").textContent()).toContain("polling " + evil);
    // the monitor log line is escaped too, and the stored record carries no query string
    expect(await page.locator("#monLog img").count()).toBe(0);
    expect(errors).toEqual([]);
  });
});
