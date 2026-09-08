// Playwright smoke for public/index.html — drives the real single-file app in headless Chromium.
// Assertions follow docs/specs/01-m0-public-blaster.md (13-19), 02-max-entropy-seeds.md (8-12),
// 03-continuous-monitoring-watchdog.md (9-12). Uses the read-only window.__hop debug hook.
import { test, expect } from "@playwright/test";

const PORT = process.env.E2E_PORT || "8765";
test.use({ baseURL: `http://127.0.0.1:${PORT}` });

const LOG_KEYS = ["seq", "ts", "level", "event", "msg", "fields"];

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

  test("Signal on: watchdog tracks hop age or resumes a suspended ctx; Signal off resets", async ({ page }) => {
    const errors = await openPage(page);
    await page.click("#power");
    await page.waitForTimeout(1500);
    const s = await state(page);
    expect(s.running).toBe(true);
    let p = await payload(page);
    if (p.audioContextState === "running") {
      expect(Number.isFinite(p.lastHopAgeMs) && p.lastHopAgeMs >= 0).toBe(true);
    } else {
      // headless without an audio sink: the watchdog must be observably attempting recovery
      await page.waitForFunction(() => window.__hop.telemetryPayload().ctxResumes >= 1, null, { timeout: 3000 });
      expect((await log(page)).some(r => r.event === "watchdog")).toBe(true);
    }
    // healthy scheduler → no false trips: shortest dwell, wait past the stall limit
    await page.evaluate(() => {
      for (const id of ["dMin", "dMax"]) { const el = document.getElementById(id); el.value = "1"; el.dispatchEvent(new Event("input")); }
    });
    p = await payload(page);
    if (p.audioContextState === "running") {
      await page.waitForTimeout(1 * 1.5 * 1000 + 1000 + 2000);
      expect((await payload(page)).watchdogTrips).toBe(0);
    }
    await page.click("#power");
    const s2 = await state(page);
    expect(s2.running).toBe(false);
    p = await payload(page);
    expect(p.lastHopAgeMs).toBeNull();
    expect(errors).toEqual([]);
  });
});
