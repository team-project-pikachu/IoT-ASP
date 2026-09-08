"""Phase: macOS / Mac Studio PWA — Vercel static control surface.

Closed-issue slice (#1, #42 family, Hold/band/platform). stdlib + pytest only.
See docs/architecture-pwa.md and tests/fixtures/issue_test_map.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT / "public" / "index.html"
VERCEL_JSON = ROOT / "vercel.json"
MANIFEST = ROOT / "public" / "manifest.webmanifest"
ARCH_DOC = ROOT / "docs" / "architecture-pwa.md"
TRACE_DOC = ROOT / "docs" / "test-traceability.md"
ISSUE_MAP = ROOT / "tests" / "fixtures" / "issue_test_map.json"


@pytest.fixture(scope="module")
def html() -> str:
    return HTML_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def vercel_cfg() -> dict:
    return json.loads(VERCEL_JSON.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def issue_map() -> dict:
    return json.loads(ISSUE_MAP.read_text(encoding="utf-8"))


def test_architecture_doc_present() -> None:
    text = ARCH_DOC.read_text(encoding="utf-8")
    for needle in (
        "Vercel PWA",
        "patch.json",
        "Hold / Manual",
        "BroadcastChannel",
        "schemaVersion",
        "area:agentic",
        "sonos-beam-2",
        "no-store",
        "Test seams",
    ):
        assert needle in text, needle
    assert "OAuth client" not in text or "does **not** invent" in text or "never invent" in text.lower() or "does not invent" in text.lower()


def test_traceability_doc_present() -> None:
    assert TRACE_DOC.is_file()
    text = TRACE_DOC.read_text(encoding="utf-8")
    assert "closed" in text.lower()
    assert "issue_test_map.json" in text


def test_vercel_json_patch_no_store(vercel_cfg: dict) -> None:
    assert vercel_cfg.get("cleanUrls") is True
    assert vercel_cfg.get("git", {}).get("deploymentEnabled", {}).get("main") is False
    headers = vercel_cfg.get("headers") or []
    patch_rules = [h for h in headers if h.get("source") == "/patch.json"]
    assert patch_rules, "patch.json header rule required"
    kv = {x["key"]: x["value"] for x in patch_rules[0]["headers"]}
    assert "no-store" in kv.get("Cache-Control", "")
    manifest_rules = [h for h in headers if h.get("source") == "/manifest.webmanifest"]
    assert manifest_rules
    global_rules = [h for h in headers if h.get("source") == "/(.*)"]
    assert global_rules
    gkv = {x["key"]: x["value"] for x in global_rules[0]["headers"]}
    assert "microphone=(self)" in gkv.get("Permissions-Policy", "")


def test_pwa_manifest() -> None:
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert m.get("name")
    assert m.get("short_name")
    assert m.get("start_url") == "/"
    assert m.get("display") == "standalone"
    assert isinstance(m.get("icons"), list) and m["icons"]
    desc = m.get("description") or ""
    assert "17" in desc and "23" in desc


def test_no_service_worker_in_public(html: str) -> None:
    assert "serviceWorker" not in html
    assert "navigator.serviceWorker" not in html
    sw_files = list((ROOT / "public").glob("**/sw.js")) + list((ROOT / "public").glob("**/service-worker.js"))
    assert sw_files == []


def test_hold_manual_and_no_browser_keys(html: str) -> None:
    assert "Hold / Manual" in html and "holdManual" in html
    assert "BACKEND_TELEMETRY_URL = \"\"" in html
    for bad in ("AIza", "sk-ant-", "VERTEX_API_KEY", "GEMINI_API_KEY"):
        assert bad not in html


def test_us_band_only_and_platform(html: str) -> None:
    assert "BAND_ABS_LO = 17000, BAND_ABS_HI = 23000" in html
    assert 'id="bandLf"' not in html
    assert "sonos-beam-2" in html
    assert "function detectPlatform(){" in html
    assert "macos-desktop" in html and "iphone" in html
    assert "mac-studio" in html


def test_patch_poll_and_beacon_seams(html: str) -> None:
    assert "async function pollPatch(){" in html
    assert "function beaconTelemetry(){" in html
    assert "setInterval(beaconTelemetry" in html
    assert "cache: \"no-store\"" in html or "cache:'no-store'" in html
    assert "BroadcastChannel" in html and "iot-asp-fleet" in html


def test_boot_setbandmode_after_logseq(html: str) -> None:
    """#1 / #139 class: deferred boot past FLEET_LOG_KEYS (TDZ)."""
    assert 'setBandMode("us"); // safe' in html
    assert html.index("const FLEET_LOG_KEYS = [") < html.index('setBandMode("us"); // safe')


def test_traceability_covers_all_closed_issues(issue_map: dict) -> None:
    closed = {int(x["issue"]) for x in issue_map["closed"]}
    # Inventory snapshot as of 2026-09-08 (gh issue list --state closed)
    expected = {
        1, 9, 12, 13, 16, 17, 19, 20, 21, 23, 34, 37, 42, 43, 44, 45, 46, 47,
        48, 49, 50, 51, 52, 53, 65, 67, 106,
    }
    missing = expected - closed
    assert not missing, f"issue_test_map missing closed issues: {sorted(missing)}"
    for entry in issue_map["closed"]:
        assert entry.get("tests"), f"#{entry['issue']} needs tests[]"
        for t in entry["tests"]:
            # scripts/ and e2e paths are allowed as opaque refs
            if t.startswith("scripts/"):
                assert (ROOT / t.split("::")[0]).is_file() or t.endswith(".sh")
                continue
            path = t.split("::")[0]
            assert (ROOT / path).is_file(), f"missing test file for #{entry['issue']}: {path}"


def test_testing_plan_links_architecture() -> None:
    plan = (ROOT / "docs" / "TESTING_PLAN.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs" / "roadmap.md").read_text(encoding="utf-8")
    assert "architecture-pwa" in plan
    assert "architecture-pwa" in roadmap
    assert "test-traceability" in plan
