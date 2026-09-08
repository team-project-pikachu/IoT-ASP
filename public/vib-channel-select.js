/**
 * Material-dependent vibration channel selection (#6).
 * Canonical twin: services/autoroute-adk/iot_asp_autoroute/vib_channel_select.py
 * Keep MATERIAL_CHANNEL_SELECT flags in sync (tests assert parity).
 *
 * Public API (globalThis.IotAspVibChannelSelect):
 *   MATERIAL_PRESETS, selectChannels(preset, opts?), allowsVibClass(sel, cls)
 *
 * #4 / #5 hooks: after detecting a vib class, call allowsVibClass before
 * updateVibClass / forceHopFromShake. Apply availability when permission
 * denied or sensor missing via selectChannels(preset, { physicalAvailable, acousticAvailable }).
 */
(function (root) {
  "use strict";

  var MATERIAL_PRESETS = ["handheld", "table", "chair", "speaker"];
  var DEFAULT_PRESET = "handheld";

  var MATERIAL_CHANNEL_SELECT = {
    handheld: {
      mode: "both",
      armPhysical: true,
      armAcoustic: true,
      prefer: "acoustic",
      setup: "Handheld / free body (acoustic-leaning)"
    },
    table: {
      mode: "physical",
      armPhysical: true,
      armAcoustic: false,
      prefer: "physical",
      setup: "Phone-on-table / rigid mount"
    },
    chair: {
      mode: "physical",
      armPhysical: true,
      armAcoustic: false,
      prefer: "physical",
      setup: "Chair-taped node 3 (infra_felt via physical)"
    },
    speaker: {
      mode: "both",
      armPhysical: true,
      armAcoustic: true,
      prefer: "acoustic",
      setup: "Soundcore enclosure contact / BT radiate (acoustic prefer)"
    }
  };

  function normalizeMaterialPreset(preset) {
    var p = String(preset || DEFAULT_PRESET).trim().toLowerCase();
    if (MATERIAL_PRESETS.indexOf(p) < 0) return DEFAULT_PRESET;
    return p;
  }

  function modeFromArms(armPhysical, armAcoustic) {
    if (armPhysical && armAcoustic) return "both";
    if (armPhysical) return "physical";
    if (armAcoustic) return "acoustic";
    return "none";
  }

  /**
   * @param {string|null|undefined} materialPreset
   * @param {{ physicalAvailable?: boolean|null, acousticAvailable?: boolean|null }} [opts]
   * @returns {{ materialPreset: string, mode: string, armPhysical: boolean, armAcoustic: boolean, prefer: string, setup: string, fallbackReason: string|null }}
   */
  function selectChannels(materialPreset, opts) {
    opts = opts || {};
    var preset = normalizeMaterialPreset(materialPreset);
    var base = MATERIAL_CHANNEL_SELECT[preset];
    var armP = !!base.armPhysical;
    var armA = !!base.armAcoustic;
    var reasons = [];

    if (opts.physicalAvailable === false && armP) {
      armP = false;
      reasons.push("physical_unavailable");
    }
    if (opts.acousticAvailable === false && armA) {
      armA = false;
      reasons.push("acoustic_unavailable");
    }

    var prefer = base.prefer;
    if (prefer === "physical" && !armP && armA) {
      prefer = "acoustic";
      reasons.push("prefer_fallback_acoustic");
    } else if (prefer === "acoustic" && !armA && armP) {
      prefer = "physical";
      reasons.push("prefer_fallback_physical");
    }

    var mode = modeFromArms(armP, armA);
    return {
      materialPreset: preset,
      mode: mode,
      armPhysical: armP,
      armAcoustic: armA,
      prefer: mode === "none" ? "none" : prefer,
      setup: base.setup,
      fallbackReason: reasons.length ? reasons.join(",") : null
    };
  }

  function allowsVibClass(selection, vibClass) {
    var cls = String(vibClass || "none").trim().toLowerCase();
    if (!cls || cls === "none") return true;
    if (cls === "physical" || cls === "infra_felt") return !!(selection && selection.armPhysical);
    if (cls === "acoustic") return !!(selection && selection.armAcoustic);
    return false;
  }

  var api = {
    MATERIAL_PRESETS: MATERIAL_PRESETS,
    MATERIAL_CHANNEL_SELECT: MATERIAL_CHANNEL_SELECT,
    DEFAULT_PRESET: DEFAULT_PRESET,
    normalizeMaterialPreset: normalizeMaterialPreset,
    selectChannels: selectChannels,
    allowsVibClass: allowsVibClass
  };

  root.IotAspVibChannelSelect = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
