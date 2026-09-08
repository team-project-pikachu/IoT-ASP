/**
 * Acoustic vib response (#5) — mic / spectrum hop-band energy burst.
 * Canonical twin: services/autoroute-adk/iot_asp_autoroute/acoustic_vib_energy.py
 *
 * Public API (globalThis.IotAspAcousticVib):
 *   WINDOW_MS, MARGIN_DB, SILENCE_DB, createTracker()
 *
 * Tracker:
 *   push(energyDb, tMs) → { median, delta, burst, silence }
 *   reset()
 *   snapshot()
 *
 * Spec (`docs/specs/04-06-vibration-channels.md` § Remaining #5):
 *   1 s rolling median of hop-band energy; burst when energy − median ≥ 12 dB.
 *   Prefer micDiff (self-TX rejected) over raw micEnergy when available.
 *   #4 owns DeviceMotion; #6 owns materialPreset / arming UI — this module
 *   only gates on an `armAcoustic` boolean passed by the caller.
 */
(function (root) {
  "use strict";

  var WINDOW_MS = 1000;
  var MARGIN_DB = 12;
  var SILENCE_DB = -90;
  var SILENCE_HOLD_MS = 800;

  function medianOf(values) {
    if (!values || !values.length) return -120;
    var sorted = values.slice().sort(function (a, b) { return a - b; });
    var mid = (sorted.length - 1) / 2;
    var lo = sorted[Math.floor(mid)];
    var hi = sorted[Math.ceil(mid)];
    return (lo + hi) / 2;
  }

  /**
   * Prefer micDiff when finite and above a floor; else raw mic/spectrum energy.
   * @param {number} energyDb
   * @param {number|null|undefined} micDiffDb
   * @returns {number}
   */
  function preferEnergy(energyDb, micDiffDb) {
    if (typeof micDiffDb === "number" && isFinite(micDiffDb) && micDiffDb > -119) {
      return micDiffDb;
    }
    if (typeof energyDb === "number" && isFinite(energyDb)) return energyDb;
    return -120;
  }

  function createTracker(opts) {
    opts = opts || {};
    var windowMs = opts.windowMs != null ? opts.windowMs : WINDOW_MS;
    var marginDb = opts.marginDb != null ? opts.marginDb : MARGIN_DB;
    var silenceDb = opts.silenceDb != null ? opts.silenceDb : SILENCE_DB;
    var silenceHoldMs = opts.silenceHoldMs != null ? opts.silenceHoldMs : SILENCE_HOLD_MS;
    var samples = [];
    var burstActive = false;
    var silenceSince = null;
    var lastT = 0;

    function prune(tMs) {
      var cutoff = tMs - windowMs;
      while (samples.length && samples[0].t < cutoff) samples.shift();
    }

    function push(energyDb, tMs) {
      var t = typeof tMs === "number" && isFinite(tMs) ? tMs : lastT;
      lastT = t;
      var e = typeof energyDb === "number" && isFinite(energyDb) ? energyDb : -120;
      samples.push({ t: t, e: e });
      prune(t);

      var median = medianOf(samples.map(function (s) { return s.e; }));
      var delta = e - median;
      var rising = delta >= marginDb && e > silenceDb;

      if (e <= silenceDb || delta < 3) {
        if (silenceSince == null) silenceSince = t;
      } else {
        silenceSince = null;
      }
      var silence = silenceSince != null && (t - silenceSince) >= silenceHoldMs;

      if (rising) burstActive = true;
      else if (silence || delta < marginDb * 0.4) burstActive = false;

      return {
        energy: e,
        median: Math.round(median * 10) / 10,
        delta: Math.round(delta * 10) / 10,
        burst: !!burstActive,
        rising: !!rising,
        silence: !!silence,
        n: samples.length
      };
    }

    function reset() {
      samples.length = 0;
      burstActive = false;
      silenceSince = null;
      lastT = 0;
    }

    function snapshot() {
      var median = medianOf(samples.map(function (s) { return s.e; }));
      return {
        median: Math.round(median * 10) / 10,
        burst: !!burstActive,
        n: samples.length,
        windowMs: windowMs,
        marginDb: marginDb
      };
    }

    return { push: push, reset: reset, snapshot: snapshot };
  }

  var api = {
    WINDOW_MS: WINDOW_MS,
    MARGIN_DB: MARGIN_DB,
    SILENCE_DB: SILENCE_DB,
    SILENCE_HOLD_MS: SILENCE_HOLD_MS,
    medianOf: medianOf,
    preferEnergy: preferEnergy,
    createTracker: createTracker
  };

  if (typeof root !== "undefined") root.IotAspAcousticVib = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
