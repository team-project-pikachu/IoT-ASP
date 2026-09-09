/**
 * Google Cast Web Sender (CAF) for IoT-ASP hop / near-ultrasonic TX.
 * Loads after window.__onGCastApiAvailable is assigned (see public/index.html).
 * Default path: Default Media Receiver + same-origin ultrasonic carrier WAV.
 * Optional custom receiver App ID via ?castAppId= / meta[name=google-cast-app-id] / localStorage.
 */
(function (global) {
  "use strict";

  var DEFAULT_CARRIER_URL = "/media/us-carrier-19khz.wav";
  var BASE_CARRIER_HZ = 19000;
  var CAST_PEAK = 0.40; // mirror Beam AirPlay digital headroom (−8 dBFS)
  var state = {
    ready: false,
    sessionActive: false,
    appId: "",
    usingDefaultReceiver: true,
    deviceName: "",
    lastLoadError: "",
    lastFreq: BASE_CARRIER_HZ,
    reloadTimer: null
  };

  function $(id) {
    return document.getElementById(id);
  }

  function qsParam(name) {
    try {
      return new URLSearchParams(location.search).get(name);
    } catch (_) {
      return null;
    }
  }

  function readAppId() {
    var fromQs = qsParam("castAppId") || qsParam("CAST_APP_ID");
    if (fromQs && String(fromQs).trim()) return String(fromQs).trim();
    var meta = document.querySelector('meta[name="google-cast-app-id"]');
    if (meta && meta.content && String(meta.content).trim()) return String(meta.content).trim();
    try {
      var stored = localStorage.getItem("hop.castAppId");
      if (stored && String(stored).trim()) return String(stored).trim();
    } catch (_) {}
    return "";
  }

  function carrierUrl() {
    var u = qsParam("castMedia") || DEFAULT_CARRIER_URL;
    try {
      return new URL(u, location.href).href;
    } catch (_) {
      return location.origin + DEFAULT_CARRIER_URL;
    }
  }

  function setStatus(text) {
    var el = $("castStatus");
    if (el) el.textContent = text;
  }

  function notifyHost(evt, detail) {
    try {
      if (typeof global.__hopOnCastEvent === "function") {
        global.__hopOnCastEvent(evt, detail || {});
      }
    } catch (_) {}
  }

  function resolveReceiverAppId() {
    var custom = readAppId();
    if (custom) {
      state.appId = custom;
      state.usingDefaultReceiver = false;
      return custom;
    }
    var defId =
      (global.chrome && chrome.cast && chrome.cast.media && chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID) ||
      "CC1AD845";
    state.appId = defId;
    state.usingDefaultReceiver = true;
    return defId;
  }

  function playbackRateForFreq(hz) {
    var f = +hz || BASE_CARRIER_HZ;
    if (!(f > 0)) f = BASE_CARRIER_HZ;
    // Keep rate in a sane Cast range; ultrasonic shift stays near 1.0 for 17–23 kHz.
    var rate = f / BASE_CARRIER_HZ;
    return Math.max(0.5, Math.min(2.0, rate));
  }

  function getSession() {
    try {
      return cast.framework.CastContext.getInstance().getCurrentSession();
    } catch (_) {
      return null;
    }
  }

  function loadCarrier(freqHz) {
    var session = getSession();
    if (!session) return Promise.reject(new Error("no session"));
    state.lastFreq = +freqHz || state.lastFreq || BASE_CARRIER_HZ;
    var url = carrierUrl();
    var mediaInfo = new chrome.cast.media.MediaInfo(url, "audio/wav");
    mediaInfo.streamType = chrome.cast.media.StreamType.BUFFERED;
    mediaInfo.metadata = new chrome.cast.media.MusicTrackMediaMetadata();
    mediaInfo.metadata.title = "IoT-ASP near-ultrasonic carrier";
    mediaInfo.metadata.artist = "hop · 17–23 kHz";
    var req = new chrome.cast.media.LoadRequest(mediaInfo);
    req.autoplay = true;
    req.currentTime = 0;
    // Receiver volume headroom (0–1). UI stays at 100%; do not blast FS into Cast.
    try {
      session.setVolume(CAST_PEAK);
    } catch (_) {}
    return session.loadMedia(req).then(function () {
      state.lastLoadError = "";
      applyPlaybackRate(state.lastFreq);
      scheduleReload();
      setStatus(
        "casting · " +
          (state.deviceName || "Chromecast") +
          " · ~" +
          Math.round(state.lastFreq) +
          " Hz · peak " +
          CAST_PEAK
      );
      notifyHost("media_loaded", { freq: state.lastFreq, url: url, peak: CAST_PEAK });
    }).catch(function (err) {
      state.lastLoadError = String(err && (err.description || err.code || err.message) || err);
      setStatus("cast load error · " + state.lastLoadError);
      notifyHost("media_error", { error: state.lastLoadError });
      throw err;
    });
  }

  function applyPlaybackRate(freqHz) {
    var session = getSession();
    if (!session) return;
    var media = session.getMediaSession();
    if (!media) return;
    var rate = playbackRateForFreq(freqHz);
    try {
      if (typeof media.setPlaybackRate === "function") {
        media.setPlaybackRate(rate);
      }
    } catch (_) {}
  }

  function scheduleReload() {
    if (state.reloadTimer) {
      clearTimeout(state.reloadTimer);
      state.reloadTimer = null;
    }
    // 2 s WAV — reload slightly early so the carrier bed stays continuous on DMR.
    state.reloadTimer = setTimeout(function () {
      if (!state.sessionActive) return;
      loadCarrier(state.lastFreq).catch(function () {});
    }, 1800);
  }

  function clearReload() {
    if (state.reloadTimer) {
      clearTimeout(state.reloadTimer);
      state.reloadTimer = null;
    }
  }

  function onSessionState(event) {
    var st = event.sessionState;
    if (
      st === cast.framework.SessionState.SESSION_STARTED ||
      st === cast.framework.SessionState.SESSION_RESUMED
    ) {
      state.sessionActive = true;
      var session = getSession();
      try {
        var dev = session && session.getCastDevice && session.getCastDevice();
        state.deviceName = (dev && (dev.friendlyName || dev.name)) || "Chromecast";
      } catch (_) {
        state.deviceName = "Chromecast";
      }
      setStatus("connected · " + state.deviceName + " · loading carrier…");
      notifyHost("session_started", {
        deviceName: state.deviceName,
        appId: state.appId,
        defaultReceiver: state.usingDefaultReceiver
      });
      loadCarrier(state.lastFreq).catch(function () {});
    } else if (st === cast.framework.SessionState.SESSION_ENDED) {
      state.sessionActive = false;
      state.deviceName = "";
      clearReload();
      setStatus("cast idle · tap Cast to pick a device");
      notifyHost("session_ended", {});
    }
  }

  function initializeCastApi() {
    if (!global.cast || !cast.framework) {
      setStatus("cast framework missing");
      return;
    }
    var appId = resolveReceiverAppId();
    cast.framework.CastContext.getInstance().setOptions({
      receiverApplicationId: appId,
      autoJoinPolicy: chrome.cast.AutoJoinPolicy.ORIGIN_SCOPED,
      resumeSavedSession: true
    });
    cast.framework.CastContext.getInstance().addEventListener(
      cast.framework.CastContextEventType.SESSION_STATE_CHANGED,
      onSessionState
    );
    state.ready = true;
    setStatus(
      state.usingDefaultReceiver
        ? "cast ready · Default Media Receiver · HTTPS Chrome/Edge"
        : "cast ready · app " + appId
    );
    notifyHost("ready", { appId: appId, defaultReceiver: state.usingDefaultReceiver });
  }

  /**
   * Called from the hop scheduler when the TX target frequency changes.
   * DMR path: nudge playbackRate on the 19 kHz carrier WAV (approximate).
   * Custom receiver path: send a simple JSON message namespace if available.
   */
  function setTone(freqHz, peak) {
    state.lastFreq = +freqHz || state.lastFreq;
    if (!state.sessionActive) return;
    applyPlaybackRate(state.lastFreq);
    var session = getSession();
    if (!session) return;
    if (peak != null) {
      try {
        session.setVolume(Math.max(0.05, Math.min(1, +peak)));
      } catch (_) {}
    }
    if (!state.usingDefaultReceiver) {
      try {
        session.sendMessage(
          "urn:x-cast:io.bearresearch.iotasp.hop",
          JSON.stringify({
            cmd: "tone",
            f: state.lastFreq,
            peak: peak != null ? +peak : CAST_PEAK,
            band: "17-23k"
          })
        );
      } catch (_) {}
    }
  }

  function getState() {
    return {
      ready: state.ready,
      sessionActive: state.sessionActive,
      appId: state.appId,
      usingDefaultReceiver: state.usingDefaultReceiver,
      deviceName: state.deviceName,
      lastLoadError: state.lastLoadError,
      lastFreq: state.lastFreq,
      peak: CAST_PEAK,
      carrierUrl: carrierUrl()
    };
  }

  global.__hopCast = {
    setTone: setTone,
    loadCarrier: loadCarrier,
    getState: getState,
    CAST_PEAK: CAST_PEAK
  };

  global.__hopOnCastReady = function () {
    try {
      initializeCastApi();
    } catch (e) {
      setStatus("cast init error · " + (e && e.message ? e.message : e));
    }
  };

  // If the Cast SDK already fired before this file loaded, init now.
  if (global.__hopCastApiAvailable) {
    global.__hopOnCastReady();
  }

  setStatus("cast loading…");
})(window);
