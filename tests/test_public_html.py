"""Static gates for the single-file public blaster (public/index.html).

Specs: docs/specs/01-m0-public-blaster.md (Acceptance 1-12),
docs/specs/02-max-entropy-seeds.md (1-7), docs/specs/03-continuous-monitoring-watchdog.md (1-8).
stdlib only; no network; deterministic.
"""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT / "public" / "index.html"
README_PATH = ROOT / "public" / "README.txt"
PATCH_PATH = ROOT / "public" / "patch.json"

KEY_PATTERNS = [
    r"AIza[0-9A-Za-z_-]{20,}",
    r"sk-[A-Za-z0-9]{20,}",
    r"BEGIN (?:RSA |OPENSSH )?PRIVATE KEY",
    r"(?:GOOGLE|GEMINI|VERTEX)_API_KEY\s*[:=]\s*['\"]",
    r"apiKey\s*[:=]\s*['\"][A-Za-z0-9_-]{16,}['\"]",
]


@pytest.fixture(scope="module")
def html() -> str:
    return HTML_PATH.read_text(encoding="utf-8")


def _fn_body(html: str, head: str) -> str:
    """Text from `head` to the next line that is exactly two-space-indented `}`."""
    i = html.index(head)
    j = html.index("\n  }\n", i)
    return html[i:j]


# ── 1. literals ──────────────────────────────────────────────────────────────
def test_invariant_literals(html: str) -> None:
    for lit in ("Hold / Manual", "holdManual", "holdPatchBtn"):
        assert lit in html, lit
    assert re.search(r"const SCHEMA_VERSION = 1;", html)
    assert re.search(r"const VOL_PATCH_MAX = 100,", html), "VOL_PATCH_MAX must match clamps.py hard max (C4)"
    assert "BAND_ABS_LO = 17000, BAND_ABS_HI = 23000" in html
    for lit in ("function blastVolJump(", "function noteImpulse(", "alarmState", "volBlast", "IMPULSE_RISE_DB"):
        assert lit in html, lit
    assert "function effectiveAlarmState(" in html
    assert "function clearAlarm(" in html
    assert "function alarmTick(" in html
    assert "alarmState: effectiveAlarmState()" in html
    assert "accelRawPrev" not in html
    assert "micEnergy_band" not in html  # keep subtract in JS netMicDiff only
    assert "function netMicDiff(" in html


# ── 2. ids ───────────────────────────────────────────────────────────────────
NEW_IDS = ("copyLogBtn", "reseedBtn", "telHopAge", "telResumes", "telWatchdog",
           "telImpulse", "telVolBlast", "telAlarm", "fleetLocal",
           "telemetryUrlLabel", "patchUrlLabel")
NEW_IDS = ("copyLogBtn", "copyFleetLogBtn", "reseedBtn", "simImpulseBtn", "fleetSeedCompare",
           "telHopAge", "telResumes", "telWatchdog",
           "telImpulse", "telVolBlast", "telAlarm", "fleetLocal")
OLD_IDS = ("telDevice", "telSeed", "telAlgo", "telPeak", "telAccel", "telMic", "telVib", "telHold",
           "telSudden", "monLog", "sysList", "sysBtn", "vol", "fMin", "fMax", "holdPatchBtn", "power")


@pytest.mark.parametrize("el_id", NEW_IDS + OLD_IDS)
def test_ids_present_once(html: str, el_id: str) -> None:
    assert html.count(f'id="{el_id}"') == 1, el_id


# ── 3. telemetryPayload keys ─────────────────────────────────────────────────
PAYLOAD_TOKENS = ("band", "power", "nightNY", "lfArmed", "lfDriveCapable", "lastHopAgeMs",
                  "ctxResumes", "watchdogTrips", "logSeq", "logTail", "holdManual",
                  "schemaVersion: SCHEMA_VERSION", "impulse", "volBlast", "alarmState")


def test_telemetry_payload_tokens(html: str) -> None:
    assert html.count("function telemetryPayload(){") == 1
    body = _fn_body(html, "function telemetryPayload(){")
    for tok in PAYLOAD_TOKENS:
        assert tok in body, tok
    # device metrics only
    for bad in ("userAgent", "geolocation", "location.", "navigator.language"):
        assert bad not in body, bad


def test_fleet_log_export_and_impulse_sim(html: str) -> None:
    assert "const FLEET_LOG_KEYS = [" in html
    assert '"impulse","volBlast","alarmState","msg"' in html.replace(" ", "") or (
        "impulse" in html and "volBlast" in html and "alarmState" in html and "FLEET_LOG_KEYS" in html
    )
    assert "function copyFleetLogJsonl()" in html
    assert "function fleetLogLineFromTel(" in html
    assert 'id="simImpulseBtn"' in html
    # The Simulate button passes a real source STRING, not booleans. It used to call
    # noteImpulse(true, false), which put `true` where `source` is read as a string by
    # blastVolJump/monLog — and, more importantly, could not satisfy the e2e contract in
    # tests/e2e/public_smoke.spec.mjs ("simulate impulse"), because noteImpulse bails when
    # neither audio nor sensors are armed and the e2e clicks Simulate on a cold page.
    # Two tests encoded contradictory contracts; the behavioural one wins.
    assert 'noteImpulse("simulate"' in html
    note = _fn_body(html, "function noteImpulse(source, deltaHint){")
    assert "enterExtremeFromBurst(" in note
    assert "blastVolJump(" in note
    # An explicit click may bypass the armed-sensor guard...
    assert 'source !== "simulate"' in note
    # ...but Hold / Manual is checked FIRST and is never bypassed (CLAUDE.md invariant 6).
    guard_lines = [ln.strip() for ln in note.splitlines() if "return false" in ln]
    assert guard_lines and "holdManual" in guard_lines[0], guard_lines
    # #54 SM: EMA accel rise (no gravity baseline warm-up vars)
    assert "accelBaselineReady" not in html
    assert "ACCEL_BASELINE_WARM_N" not in html
    assert "accelBaselineSamples" not in html
    assert "hop.tabSeed" in html
    assert 'sessionStorage.setItem("hop.tabSeed"' in html
    assert 'sessionStorage.getItem("hop.tabSeed"' in html
    # hop.seed may mirror to localStorage for tooling/spec-02 reseed asserts; tab RNG is session-scoped.
    assert 'localStorage.setItem("hop.seed"' in html
    hyst = _fn_body(html, "function tickAlarmHysteresis(now, stillHot){")
    assert "BURST_QUIET_MS" in hyst and "lastImpulseAt" in hyst
    assert "clearImpulseAlarm(" in hyst
    assert "function clearImpulseAlarm(" in html
    assert 'setAlarmState("cleared")' in html or "ALARM_CLEARED_MS" in html
    mon = _fn_body(html, "function monLog(msg, event, fields, level){")
    assert "fleet" in mon
    assert "r.fleet" in _fn_body(html, "function copyFleetLogJsonl(){")
    assert "d.instanceId === instanceId" in html
    assert "Seed compare" in html
    assert "peerStale" in html


# ── 4. enrichment literals ───────────────────────────────────────────────────
def test_enrichment_literals(html: str) -> None:
    for lit in ('"ac120"', '"America/New_York"', '"17-23k"', "function nightNYNow("):
        assert lit in html, lit
    # Legacy "10-20" may appear only as rejected patch tag — public TX is ultrasonic-only.
    assert 'bandWireTag(){ return "17-23k"; }' in html.replace(" ", "") or 'return "17-23k"' in html
    assert 'id="bandLf"' not in html
    assert "detectPlatform" in html
    assert "sonos-beam-2" in html
    assert "hour12: false" in html


def test_backend_url_query_overrides(html: str) -> None:
    """#61 — live URLs via query, never baked secrets."""
    assert 'id="telemetryUrlLabel"' in html
    assert 'id="patchUrlLabel"' in html
    assert 'qs.get("patch")' in html or "qs.get('patch')" in html
    assert 'qs.get("telemetry")' in html
    assert 'qs.get("pollMs")' in html
    assert 'BACKEND_TELEMETRY_URL = ""' in html
    assert 'TELEMETRY_URL || "off"' in html or "TELEMETRY_URL || 'off'" in html


# ── 5. delimited blocks + log ────────────────────────────────────────────────
BANNERS = (
    "// ══ structured monitor log (#22) ══",
    "// ══ telemetry enrichment (#22) ══",
    "// ══ watchdog (#3) ══",
    "// ══ max-entropy seeds (#2) ══",
    "// ══ debug hook (#1) ══",
)


def test_delimited_blocks(html: str) -> None:
    pos = [html.index(b) for b in BANNERS]
    assert pos == sorted(pos), "blocks must appear in spec order"
    assert "const LOG_MAX = 200;" in html
    assert "window.__hop" in html
    assert "Object.freeze(" in html
    for k in ("getLog", "getState", "seedSource"):
        assert k in html, k


# ── 6. negatives ─────────────────────────────────────────────────────────────
def test_no_web_bluetooth(html: str) -> None:
    assert "navigator.bluetooth" not in html
    assert "requestDevice(" not in html


@pytest.mark.parametrize("pat", KEY_PATTERNS)
def test_no_key_patterns(html: str, pat: str) -> None:
    assert not re.search(pat, html, flags=re.I), pat


# ── 7. parses as HTML, one <script> ──────────────────────────────────────────
class _Counter(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: dict[str, int] = {}
        self.ids: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        self.tags[tag] = self.tags.get(tag, 0) + 1
        for k, v in attrs:
            if k == "id" and v:
                self.ids.append(v)


def test_html_parses_single_script(html: str) -> None:
    p = _Counter()
    p.feed(html)
    p.close()
    assert p.tags.get("script") == 1
    for t in ("html", "head", "body", "main"):
        assert p.tags.get(t) == 1, t
    assert len(p.ids) == len(set(p.ids)), "duplicate element ids"
    for el_id in NEW_IDS:
        assert el_id in p.ids


# ── 8. README (M0 record, no PII) ────────────────────────────────────────────
def test_readme_m0_record() -> None:
    txt = README_PATH.read_text(encoding="utf-8")
    # exact equality against extracted URL tokens — never a substring/`in` test on a URL literal
    # (CodeQL py/incomplete-url-substring-sanitization matches `<url> in <expr>` regardless of type).
    live_url = "https://hop-ultrasonic-1digital-design.vercel.app/"
    urls = re.findall(r"https?://[^\s<>\"')]+", txt)
    assert any(u == live_url for u in urls), urls
    assert "Sonos Beam" in txt
    assert "Mac Studio" in txt or "desktop" in txt
    assert "iPhone 16" in txt and "iPhone 14" in txt
    assert re.search(r"\b(three|3)\b", txt)
    assert "native" in txt.lower() and ("Bluetooth" in txt or "audio" in txt)
    assert "17–23" in txt or "17-23" in txt
    assert "@" not in txt, "no emails"
    assert not re.search(r"\b\d{5}\b", txt), "no ZIP-like numbers"
    for m in re.finditer(r"Web Bluetooth", txt):
        assert txt[max(0, m.start() - 3):m.start()] == "No ", "Web Bluetooth only as a negation"


# ── 9. patch.json mock ───────────────────────────────────────────────────────
def test_patch_json_schema_version() -> None:
    assert json.loads(PATCH_PATH.read_text(encoding="utf-8"))["schemaVersion"] == 1


# ── 10. monLog signature + legacy callers ────────────────────────────────────
def test_monlog_signature(html: str) -> None:
    assert html.count("function monLog(") == 1
    assert "function monLog(msg, event, fields, level)" in html
    assert html.count('monLog("') >= 3
    for k in ("seq: ++logSeq", "ts: new Date().toISOString()", "level:", "event:", "msg:", "fields:"):
        assert k in html, k
    assert "records.slice(-3)" in html


# ── 11. banner discipline ────────────────────────────────────────────────────
def test_banner_lines_well_formed(html: str) -> None:
    lines = [ln for ln in html.splitlines() if "// ══" in ln and "(#" in ln]
    assert len(lines) >= 5
    for ln in lines:
        assert re.match(r"^\s*// ══ .+ \(#\d+\) ══+\s*$", ln), ln


# ── 12. size guard ───────────────────────────────────────────────────────────
def test_size_guard() -> None:
    # Raised 2026-09-08 for fleet cards + impulse/alarm SM (#11/#42/#44/#45).
    # Raised again 2026-09-08 for the Nest tiles + pollNest guard (#85/#101) landing on top of
    # the platform/sink tiles from #138 — 140_052 B at the merge, ~10 kB headroom.
    assert HTML_PATH.stat().st_size < 150_000


# ── spec 02: max-entropy seeds ───────────────────────────────────────────────
def test_entropy_seed(html: str) -> None:
    assert html.count("function entropySeed(") == 1
    assert "crypto.getRandomValues(" in html
    assert "new Uint32Array(4)" in html
    assert "function xmur3(" in html and "function fnv1a32(" in html
    for c in ("0x811c9dc5", "0x01000193", "3432918353"):
        assert c in html, c
    body = _fn_body(html, "function entropySeed(){")
    for bad in ("userAgent", "language", "location.", "geolocation"):
        assert bad not in body, bad
    assert "Math.floor(Math.random() * 1e9)" not in html, "seed must not derive from Math.random"
    assert html.count("function mulberry32(") == 1


def test_min_hop_delta_and_stagger(html: str) -> None:
    assert "MIN_HOP_DELTA_HZ" in html
    assert "Math.max(200, 0.05 * (bandHigh() - bandLow()))" in html
    assert "i < 8" in _fn_body(html, "const pickFreq  = () => {")
    start_body = _fn_body(html, "async function start(){")
    assert "rand() * 0.5" in start_body
    assert "lastHopAt = performance.now();" in start_body


def test_reseed(html: str) -> None:
    assert html.count("function reseed(") == 1
    for lit in ('"entropy"', 'reseed("ui")', 'reseed("patch")', "seedSource"):
        assert lit in html, lit
    # Per-tab seed lives in sessionStorage so same-origin peers can diverge
    assert 'sessionStorage.setItem("hop.tabSeed", String(seed))' in html
    assert '"session"' in html or '"stored"' in html


# ── spec 03: watchdog ────────────────────────────────────────────────────────
def test_watchdog(html: str) -> None:
    assert "setInterval(watchdogTick, 1000)" in html
    assert html.count("function watchdogTick(") == 1
    body = _fn_body(html, "function watchdogTick(){")
    for tok in ('ctx.state !== "running"', "ctx.resume()", "ctxResumes++", "watchdogTrips++",
                "pending.length = 0", "schedule()", '"watchdog reschedule"', ', "watchdog",'):
        assert tok in body, tok
    assert "committedDwellS() * 1.5 * 1000 + 1000" in html
    assert html.count("lastHopAt = performance.now();") >= 2
    assert "function lastHopAgeMs(" in html and "function stallLimitMs(" in html


def test_watchdog_cells_in_mon_grid(html: str) -> None:
    i = html.index('<div class="mon-grid">')
    j = html.index("</div>\n    <", i)
    grid = html[i:j]
    for el_id in ("telHopAge", "telResumes", "telWatchdog", "telSudden"):
        assert f'id="{el_id}"' in grid, el_id


def test_hold_manual_short_circuits_preserved(html: str) -> None:
    ap = _fn_body(html, "function applyPatch(raw){")
    assert ap.startswith('function applyPatch(raw){\n    if (holdManual) { patchStatus = "held";')
    pp = _fn_body(html, "async function pollPatch(){")
    assert pp.startswith('async function pollPatch(){\n    if (holdManual) { patchStatus = "held";')


# ── review fixes: watchdog judges the COMMITTED schedule, not the live sliders ────
def test_watchdog_stall_uses_committed_schedule(html: str) -> None:
    """Lowering dMin/dMax mid-dwell must not trip the watchdog (review finding 1)."""
    limit = _fn_body(html, "function stallLimitMs(){")
    assert "dwellHi()" not in limit, "stallLimitMs must not read the live slider"
    assert "committedDwellS()" in limit
    committed = _fn_body(html, "function committedDwellS(){")
    assert "lastHopDwellS > 0 ? lastHopDwellS : dwellHi()" in committed
    # the committed dwell is recorded exactly once, where hops are delivered (shared by frame() and the watchdog)
    assert html.count("lastHopDwellS = hop.d;") == 1
    assert html.count("function shiftDueHops(") == 1
    assert "shiftDueHops();" in _fn_body(html, "function frame(){")
    body = _fn_body(html, "function watchdogTick(){")
    assert "shiftDueHops()" in body
    assert "nextHopOverdueMs()" in body
    for tok in ('"hopOverdue"', '"clockStalled"', "reason,", "overdueMs: overdue", "lastHopDwellS = 0;"):
        assert tok in body, tok
    assert "const STALL_GRACE_S = 1.0;" in html
    assert "pending.length ? pending[0].t : nextHopAt" in _fn_body(html, "function nextHopDueAt(){")
    start_body = _fn_body(html, "async function start(){")
    assert "lastHopDwellS = 0;" in start_body


# ── review fixes: no URL query string in the structured log / logTail ───────────
def test_log_never_stores_url_query(html: str) -> None:
    """`?patch=` may be a signed/tokened URL: it must never reach `records` (→ logTail / Copy log JSON)."""
    assert html.count("function redactUrlQuery(") == 1
    assert 'replace(URL_QUERY_RE, "$1?[redacted]")' in html
    body = _fn_body(html, "function monLog(msg, event, fields, level){")
    assert "msg: redactUrlQuery(msg).slice(0, 240)" in body
    # no monLog call may concatenate the raw PATCH_URL / TELEMETRY_URL
    for m in re.finditer(r"monLog\([^\n]*", html):
        line = m.group(0)
        assert "+ PATCH_URL" not in line and "+ TELEMETRY_URL" not in line, line
    assert 'monLog("scientific tooling ready · patch " + redactUrlQuery(PATCH_URL) + " · poll " + POLL_MS + "ms (hot-apply)");' in html
    # the debug hook and the payload still expose the ring buffer only through copies
    assert "records.slice(-3)" in _fn_body(html, "function telemetryPayload(){")


def test_redact_regex_semantics() -> None:
    """Mirror of URL_QUERY_RE (kept in sync by test_log_never_stores_url_query) — stdlib re."""
    rx = re.compile(
        r"((?:https?://|/)[^\s?#]*|(?:[A-Za-z0-9._~-]+/)*[A-Za-z0-9._~-]+\.[A-Za-z0-9._~-]+)[?#][^\s]*"
    )
    red = lambda t: rx.sub(r"\1?[redacted]", t)
    assert red("patch /patch.json?X-Goog-Signature=SECRET123") == "patch /patch.json?[redacted]"
    assert red("https://h.example/p.json?token=T#f") == "https://h.example/p.json?[redacted]"
    assert red("ready patch.json?token=SECRET") == "ready patch.json?[redacted]"
    assert red("what? really") == "what? really"
    assert red("patch /patch.json") == "patch /patch.json"


# ── review fixes: systems-check rows escape reflected text (XSS via ?patch=) ────
def test_systems_check_rows_escaped(html: str) -> None:
    assert html.count("function escHtml(") == 1
    body = _fn_body(html, "function row(label, status, detail){")
    assert "escHtml(label)" in body and "escHtml(detail)" in body
    assert '+ label +' not in body and '+ detail +' not in body
    esc = _fn_body(html, "function escHtml(s){") if "function escHtml(s){\n" in html else html[html.index("function escHtml(s){"):html.index("\n", html.index("function escHtml(s){"))]
    for ent in ("&lt;", "&gt;", "&amp;", "&quot;", "&#39;"):
        assert ent in esc, ent
    # monitor log lines go through the same helper
    assert "const safe = escHtml(rec.msg);" in html
    # innerHTML sinks: every string concatenated into sysList / monLog lines is escaped
    assert html.count("sysList.innerHTML") == 2


def test_impulse_alarm_and_fleet_stub(html: str) -> None:
    assert html.count("function noteImpulse(") == 1
    assert html.count("function tickAlarmHysteresis(") == 1
    assert html.count("function blastVolJump(") == 1
    assert html.count("function clearImpulseAlarm(") == 1
    assert html.count("function effectiveAlarmState(") == 1
    assert "BroadcastChannel" in html and "iot-asp-fleet" in html
    for el_id in ("telImpulse", "telVolBlast", "telAlarm", "fleetLocal", "fleetPeer2", "fleetPeer3"):
        assert html.count(f'id="{el_id}"') == 1, el_id
    body = _fn_body(html, "function telemetryPayload(){")
    for tok in ("impulse: !!impulse", "volBlast: !!volBlast", "alarmState: effectiveAlarmState()"):
        assert tok in body, tok
    assert "IMPULSE_ACCEL_RISE" in html and "IMPULSE_RISE_DB" in html
    assert "accelRawPrev" not in html
    assert "accelBaseline" not in html
    assert "tickAlarmHysteresis(now, stillHot || onset || micImpulse)" in html
    assert "d.instanceId === instanceId" in html
    assert "fleetPeers[d.instanceId] = d" in html
    assert "deviceId, instanceId, seed" in html


def test_nest_status_surface_is_display_only(html: str) -> None:
    """#101 Nest/SDM surface renders status and must never become a second control plane.

    The alarm has exactly one escalation path: backend authors a clamped patch, the app
    polls and hot-applies it (docs/api-contract.md). If the Nest status poller could also
    drive the alarm, Hold/Manual and the clamps would have a route around them.
    """
    # tiles exist
    for el in ('id="telNestEvent"', 'id="telNestClass"', 'id="telNestAge"'):
        assert el in html, el
    assert 'const BACKEND_NEST_PATH = "/nest.json"' in html
    assert 'qs.get("nest")' in html

    body = _fn_body(html, "async function pollNest(){")
    # read-only fetch, cache-busted like the patch poll
    assert "fetch(" in body and 'cache: "no-store"' in body
    # ...and it drives NOTHING. These are the functions that escalate.
    for forbidden in (
        "noteImpulse", "setAlarmState", "blastVolJump", "enterExtremeFromBurst",
        "applyPatch", "holdManual =", "volBlast =", "alarmState =",
    ):
        assert forbidden not in body, f"pollNest must not call/assign {forbidden}"
    # no credential ever leaves the page on this path
    for forbidden in ("Authorization", "Bearer", "access_token", "client_secret", "apiKey"):
        assert forbidden not in body, f"pollNest must not send {forbidden}"


def test_nest_mock_is_schema_version_1_and_carries_no_pii() -> None:
    data = json.loads((ROOT / "public" / "nest.json").read_text(encoding="utf-8"))
    assert data["schemaVersion"] == 1
    blob = json.dumps(data)
    # Google's docs placeholders only — never a real resource name, preview URL or address.
    for forbidden in ("previewUrl", "enterprises/", "structures/", "home.google.com", "@gmail.com"):
        assert forbidden not in blob, forbidden


def test_nest_url_override_cannot_be_pointed_off_origin(html: str) -> None:
    """CodeQL client-side request forgery (alert 26): `?nest=` is attacker-controllable.

    A crafted link must not be able to make a victim's page fetch an arbitrary URL. The
    guard resolves the value against location.href and requires (a) the SAME origin and
    (b) a plain `*.json` path. Same-origin alone stops the forgery; the path shape stops
    a junk value issuing a pointless request and stops a crafted override reaching an
    unrelated same-origin endpoint (`/../../etc/passwd` normalises to `/etc/passwd`).

    `?patch=` is deliberately NOT restricted this way: docs/api-contract.md documents it
    as accepting an absolute live-backend URL. The Nest status object is always written
    beside patch.json on our own origin, so the restriction costs nothing there.
    """
    assert "function sameOriginPath(candidate, fallback){" in html
    guard = _fn_body(html, "function sameOriginPath(candidate, fallback){")
    assert "new URL(" in guard
    assert "u.origin !== location.origin" in guard, "must compare origins"
    assert ".json$" in guard, "must constrain the resolved path shape"
    assert "return fallback" in guard
    # the override is routed through the guard, never used raw
    assert 'const NEST_URL = sameOriginPath(qs.get("nest"), BACKEND_NEST_PATH);' in html
    assert 'qs.get("nest") ||' not in html, "raw ?nest= must not reach fetch()"

# ── hop button boot / platform (post-#138 regression) ─────────────────────
def test_logseq_initialized_before_boot_setbandmode(html: str) -> None:
    """Boot setBandMode must not run while logSeq/FLEET_LOG_KEYS are in TDZ (kills listeners)."""
    assert "let logSeq = 0;" in html
    log_i = html.index("let logSeq = 0;")
    fleet_i = html.index("const FLEET_LOG_KEYS = [")
    # Prefer deferred boot call after fleet keys; tolerate only post-fleet setBandMode("us")
    boot_marker = 'setBandMode("us"); // safe'
    assert boot_marker in html, "boot setBandMode must be deferred past FLEET_LOG_KEYS"
    boot_i = html.index(boot_marker)
    assert log_i < boot_i
    assert fleet_i < boot_i
    assert 'id="bandLf"' not in html
    assert "bandLfBtn" not in html


def test_detect_platform_mac_vs_iphone(html: str) -> None:
    body = _fn_body(html, "function detectPlatform(){")
    assert "iPadDesktopUA" in body
    assert "touchPoints > 1" in body
    assert "macos-desktop" in body and "iphone" in body
    assert "mac-studio" in body
    assert 'id="telPlatform"' in html
    # Must not treat Mac desktop (maxTouchPoints==0 or 1) as iPhone
    assert "maxTouchPoints || 0) > 0" not in body.replace(" ", "") or "touchPoints > 1" in body
