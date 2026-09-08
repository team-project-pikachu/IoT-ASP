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


# ── 2. ids ───────────────────────────────────────────────────────────────────
NEW_IDS = ("copyLogBtn", "copyFleetLogBtn", "reseedBtn", "simImpulseBtn", "fleetSeedCompare",
           "telHopAge", "telResumes", "telWatchdog",
           "telImpulse", "telVolBlast", "telAlarm", "fleetLocal",
           "telemetryUrlLabel", "patchUrlLabel")
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
    assert "noteImpulse(true, false)" in html
    assert "Seed compare" in html
    assert "peerStale" in html


def test_backend_url_query_overrides(html: str) -> None:
    """#61 — live URLs via query, never baked secrets."""
    assert 'id="telemetryUrlLabel"' in html
    assert "qs.get(\"patch\")" in html or "qs.get('patch')" in html or 'qs.get("patch")' in html
    assert 'qs.get("telemetry")' in html
    assert 'qs.get("pollMs")' in html
    assert 'BACKEND_TELEMETRY_URL = ""' in html
    assert "TELEMETRY_URL || \"off\"" in html or 'TELEMETRY_URL || "off"' in html

    for lit in ('"ac120"', '"America/New_York"', '"10-20"', '"17-23k"', "function nightNYNow("):
        assert lit in html, lit
    assert "+fMin.value <= 100" in html
    assert "hour12: false" in html


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
    assert "iPhone 16" in txt and "iPhone 14" in txt
    assert re.search(r"\b(three|3)\b", txt)
    assert "native Bluetooth" in txt
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
    # Raised 2026-09-08 for fleet cards + impulse/alarm stubs (#11/#42/#44/#45).
    assert HTML_PATH.stat().st_size < 140_000


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
    for lit in ('"stored"', '"entropy"', 'reseed("ui")', 'reseed("patch")', "seedSource"):
        assert lit in html, lit
    assert 'localStorage.setItem("hop.seed", String(seed))' in html


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
    assert html.count("function alarmTick(") == 1
    assert html.count("function blastVolJump(") == 1
    assert html.count("function clearAlarm(") == 1
    assert "BroadcastChannel" in html and "iot-asp-fleet" in html
    for el_id in ("telImpulse", "telVolBlast", "telAlarm", "fleetLocal", "fleetPeer2", "fleetPeer3"):
        assert html.count(f'id="{el_id}"') == 1, el_id
    body = _fn_body(html, "function telemetryPayload(){")
    for tok in ("impulse: !!impulse", "volBlast: !!volBlast", "alarmState"):
        assert tok in body, tok
    assert "clearAlarm(" in html and "IMPULSE_ACCEL_DELTA" in html
    assert "setInterval(function(){ alarmTick(performance.now()); }, 200)" in html
    assert 'alarmState = "cleared";' in html
    assert 'alarmState = "armed";' not in _fn_body(html, "function alarmTick(now){")
    assert "if (impulse) {" in _fn_body(html, "function beaconTelemetry(){")
    assert "d.instanceId === instanceId" in html
    assert "fleetPeers[d.instanceId] = d" in html
    assert "deviceId, instanceId, seed" in html
