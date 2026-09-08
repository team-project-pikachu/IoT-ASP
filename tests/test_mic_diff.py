"""Tests for iot_asp_autoroute.mic_diff — #25 HW-limited LF mic/TX + AEC micDiff.

Offline, deterministic (random.Random(25), fixed values). IDs mirror
docs/specs/25-hw-limited-lf-aec-micdiff.md § Acceptance tests (MD-01 … MD-19).
"""

from __future__ import annotations

import copy
import json
import os
import random
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "services" / "autoroute-adk"
sys.path.insert(0, str(PKG_DIR))

from iot_asp_autoroute import clamps, priors  # noqa: E402
from iot_asp_autoroute import mic_diff as md  # noqa: E402

IOS_SAFARI_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)
IOS_CHROME_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/604.1"
)
DESKTOP_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

BASE_PATCH = {
    "schemaVersion": 1,
    "algo": "hop",
    "fMin": 17000,
    "fMax": 23000,
    "vol": 8,
    "shriekMs": 110,
    "rationale": "x",
}


def _extreme_decision(mic_diff_db: float = 9.0) -> dict:
    return md.burst_decision(mic_diff_db)


# ── MD-01 constants ──────────────────────────────────────────────────────────


def test_md01_constants():
    assert md.MIC_DIFF_ALPHA == 0.85
    assert md.MIC_DIFF_THR_DB == 6.0
    assert md.ALPHA_RANGE == (0.0, 2.0)
    assert md.MIN_CAL_PAIRS == 3
    assert md.SHRIEK_MS_BIAS == 15
    assert md.BURST_ALGO in clamps.ALLOWED_ALGOS
    assert md.WEB_SAMPLE_HZ / md.MIC_FFT_SIZE == pytest.approx(23.4375)
    assert clamps.CLAMPS["vol_hard_max"] == clamps.CLAMPS["vol_soft_max"] == 100.0


# ── MD-02 math ───────────────────────────────────────────────────────────────


def test_md02_math():
    assert md.mic_diff(-20.0, -30.0) == pytest.approx(5.5)
    assert md.mic_diff(-20.0, -30.0, alpha=1.0) == pytest.approx(10.0)
    assert md.mic_diff(0.0, -30.0) == pytest.approx(25.5)
    out = md.mic_diff(-20.12345, -30.98765)
    assert isinstance(out, float)
    assert out == round(-20.12345 - 0.85 * -30.98765, 3)
    assert len(repr(out).split(".")[-1]) <= 3


# ── MD-03 passthrough ────────────────────────────────────────────────────────


def test_md03_passthrough():
    assert md.mic_diff(-20.0, None) == -20.0
    assert md.mic_diff(-20.0, "x") == -20.0
    assert md.mic_diff(-20.0, -30.0, alpha=0.0) == -20.0
    assert md.mic_diff(None, -30.0) == pytest.approx(25.5)
    assert md.mic_diff(float("nan"), -30.0) == pytest.approx(25.5)
    assert md.mic_diff(-20.0, -30.0, alpha=None) == pytest.approx(5.5)
    assert md.mic_diff(-20.0, -30.0, alpha=float("inf")) == pytest.approx(5.5)
    assert md.mic_diff_from_telemetry({"micDiff": 7.25, "micEnergy": -20, "outLevel": -30}) == 7.25
    assert md.mic_diff_from_telemetry({"micEnergy": -20, "outLevel": -30}) == pytest.approx(5.5)
    assert md.mic_diff_from_telemetry({"micEnergy": -20}) == pytest.approx(-20.0)
    assert md.mic_diff_from_telemetry({"outLevel": -30}) is None
    assert md.mic_diff_from_telemetry({}) is None
    assert md.mic_diff_from_telemetry(None) is None
    assert md.mic_diff_from_telemetry({"micDiff": float("nan"), "micEnergy": -20, "outLevel": -30}) == pytest.approx(5.5)


# ── MD-04 calibration recovers alpha ─────────────────────────────────────────


def test_md04_calibration_recovers_alpha():
    rng = random.Random(25)
    pairs = []
    for _ in range(20):
        out = -40.0 + 30.0 * rng.random()
        pairs.append((0.85 * out + rng.gauss(0.0, 0.5), out))
    r = md.calibrate_alpha(pairs)
    assert r["ok"] is True
    assert abs(r["alpha"] - 0.85) < 0.1
    assert r["n"] == 20
    assert 0 <= r["residual_rms"] < 1.0
    assert r["clamped"] is False
    assert r["reason"] == "ok"

    exact = [(-8.5 * k, -10.0 * k) for k in range(1, 6)]
    r2 = md.calibrate_alpha(exact)
    assert r2["ok"] is True
    assert r2["alpha"] == pytest.approx(0.85, abs=1e-9)
    assert r2["residual_rms"] == pytest.approx(0.0, abs=1e-9)
    assert r2["n"] == 5


# ── MD-05 alpha clamp ────────────────────────────────────────────────────────


def test_md05_alpha_clamp():
    hi = md.calibrate_alpha([(-100, -10), (-200, -20), (-300, -30)])  # slope 10
    assert hi["ok"] is True
    assert hi["alpha"] == 2.0
    assert hi["clamped"] is True
    assert hi["reason"].startswith("alpha clamped")
    assert hi["residual_rms"] is not None and hi["residual_rms"] > 0

    lo = md.calibrate_alpha([(30, -10), (60, -20), (90, -30)])  # slope -3
    assert lo["ok"] is True
    assert lo["alpha"] == 0.0
    assert lo["clamped"] is True


# ── MD-06 refusal ────────────────────────────────────────────────────────────


def test_md06_refusal():
    cases = [
        ([], 0),
        ([(-20, -30), (-21, -31)], 2),
        ([(-20, None), ("a", -30), (-21, -31), (-22, -32)], 2),
    ]
    for pairs, n in cases:
        snapshot = copy.deepcopy(pairs)
        r = md.calibrate_alpha(pairs)
        assert r["ok"] is False
        assert r["alpha"] == 0.85
        assert r["residual_rms"] is None
        assert r["reason"].startswith("need >= 3")
        assert r["n"] == n
        assert pairs == snapshot

    zero = md.calibrate_alpha([(-20, 0), (-21, 0), (-22, 0)])
    assert zero["ok"] is False
    assert zero["reason"] == "outLevel has no variance"
    assert zero["alpha"] == 0.85
    assert zero["n"] == 3

    # Garbage rows (not 2-tuples) are dropped, not raised on.
    junk = md.calibrate_alpha([None, 5, "ab", (1, 2, 3)])
    assert junk["ok"] is False and junk["n"] == 0


# ── MD-07 monotonicity vs thr ────────────────────────────────────────────────


def test_md07_monotonic_extreme_vs_threshold():
    by_thr = [md.burst_decision(6.5, thr_db=t)["extreme"] for t in (0, 3, 6, 6.4, 6.5, 6.6, 9, 20)]
    assert by_thr == [True, True, True, True, False, False, False, False]
    assert all(a >= b for a, b in zip(by_thr, by_thr[1:]))  # non-increasing

    by_md = [md.burst_decision(m)["extreme"] for m in (-10, 0, 5.9, 6.0, 6.01, 10, 40)]
    assert by_md == [False, False, False, False, True, True, True]
    assert all(a <= b for a, b in zip(by_md, by_md[1:]))  # non-decreasing (strict >)


# ── MD-08 extreme payload ────────────────────────────────────────────────────


def test_md08_extreme_payload():
    d = md.burst_decision(9.0, vib_class="physical")
    assert d["extreme"] is True
    assert d["algo"] == "shriek_chirp"
    assert d["shriekMsBias"] == 15
    assert d["vibClass"] == "physical"
    assert "9.0" in d["reason"]
    assert list(d) == ["extreme", "algo", "shriekMsBias", "thrDb", "micDiffDb", "vibClass", "reason"]

    q = md.burst_decision(2.0)
    assert q["extreme"] is False and q["algo"] is None and q["shriekMsBias"] == 0
    assert md.burst_decision(None)["reason"] == "micDiff unavailable"
    assert md.burst_decision(float("inf"))["extreme"] is False
    assert md.burst_decision(float("nan"))["reason"] == "micDiff unavailable"
    assert md.burst_decision(9.0, vib_class="bogus")["vibClass"] == "none"
    assert md.burst_decision(9.0, thr_db="junk")["thrDb"] == 6.0  # bad thr → default


# ── MD-09 holdManual refuse ──────────────────────────────────────────────────


def test_md09_hold_manual_refuses():
    for value in (None, -10, 0, 6.01, 40, 1e9):
        d = md.burst_decision(value, hold_manual=True)
        assert d["extreme"] is False
        assert d["algo"] is None
        assert d["shriekMsBias"] == 0
        assert d["reason"] == "holdManual — refuse"
    t = {"holdManual": True, "soundBurst": True, "extremeActive": True, "micDiff": 40}
    assert md.burst_decision_from_telemetry(t)["extreme"] is False
    assert md.burst_decision_from_telemetry({"holdManual": True, "micDiff": 40})["reason"] == "holdManual — refuse"
    # apply_burst_bias on a refused decision is a no-op.
    out = md.apply_burst_bias(BASE_PATCH, md.burst_decision(40, hold_manual=True))
    assert out == BASE_PATCH and "burstBias" not in out


# ── MD-10 telemetry flags ────────────────────────────────────────────────────


def test_md10_telemetry_flags():
    d = md.burst_decision_from_telemetry({"soundBurst": True, "micEnergy": -40, "outLevel": -30})
    assert d["extreme"] is True
    assert d["reason"].startswith("soundBurst/extremeActive flag")
    assert d["micDiffDb"] == pytest.approx(-14.5)
    assert d["algo"] == "shriek_chirp" and d["shriekMsBias"] == 15

    d2 = md.burst_decision_from_telemetry({"extremeActive": True})
    assert d2["extreme"] is True and d2["micDiffDb"] is None

    assert md.burst_decision_from_telemetry({"micEnergy": -12, "outLevel": -30})["extreme"] is True
    assert md.burst_decision_from_telemetry({"micEnergy": -20, "outLevel": -30})["extreme"] is False
    assert md.burst_decision_from_telemetry({"soundBurst": "yes"})["extreme"] is False
    assert md.burst_decision_from_telemetry({})["reason"] == "micDiff unavailable"
    assert md.burst_decision_from_telemetry(None)["extreme"] is False


# ── MD-11 apply_burst_bias within clamps ─────────────────────────────────────


def test_md11_apply_burst_bias_within_clamps():
    base = copy.deepcopy(BASE_PATCH)
    snapshot = copy.deepcopy(base)
    out = md.apply_burst_bias(base, _extreme_decision(9.0))
    assert out["algo"] == "shriek_chirp"
    assert out["shriekMs"] == 120.0
    assert out["rationale"].endswith("burst→shriek_chirp (+15 ms)")
    assert out["burstBias"] == {"micDiffDb": 9.0, "shriekMsBias": 15}
    assert (out["fMin"], out["fMax"], out["vol"]) == (17000, 23000, 8)
    assert base == snapshot
    ok, msg, clamped = clamps.validate_patch(out)
    assert ok is True, msg
    assert clamped["shriekMs"] == 120.0 and clamped["band"] == "17-23k"

    assert md.apply_burst_bias({**base, "shriekMs": 50}, _extreme_decision())["shriekMs"] == 65.0
    no_shriek = {k: v for k, v in base.items() if k != "shriekMs"}
    out2 = md.apply_burst_bias(no_shriek, _extreme_decision())
    assert out2["shriekMs"] == 65.0
    assert clamps.validate_patch(out2)[0] is True
    no_rat = {k: v for k, v in base.items() if k != "rationale"}
    assert md.apply_burst_bias(no_rat, _extreme_decision())["rationale"] == "burst→shriek_chirp (+15 ms)"

    quiet = md.apply_burst_bias(base, md.burst_decision(2.0))
    assert quiet == base and "burstBias" not in quiet
    assert quiet is not base


# ── MD-12 aec_capability ─────────────────────────────────────────────────────


def test_md12_aec_capability():
    expected = [
        (None, "unknown"),
        ("", "unknown"),
        (IOS_SAFARI_UA, "ios-safari"),
        (IOS_CHROME_UA, "ios-chrome"),
        (DESKTOP_CHROME_UA, "other"),
    ]
    for ua, cls in expected:
        out = md.aec_capability(ua)
        assert out["fullAEC"] is False
        assert out["path"] == "output-bus-subtraction"
        assert out["alpha"] == 0.85
        assert "#9" in out["nativePath"]
        assert "docs/iphone-bluetooth.md" in out["docs"]
        assert out["userAgentClass"] == cls
        assert "Mozilla" not in json.dumps(out)
        assert "advisory" in out["reason"]
    assert md.aec_capability()["userAgentClass"] == "unknown"


# ── MD-13 lf_capability ──────────────────────────────────────────────────────


def test_md13_lf_capability():
    none = md.lf_capability(None)
    assert none["lfTx"] is False and none["lfMic"] is False

    cap = md.lf_capability({"lfDriveCapable": True})
    assert cap["lfTx"] is True and cap["lfMic"] is False
    assert "lfTx: lfDriveCapable asserted by telemetry" in cap["reasons"]

    hold = md.lf_capability({"lfDriveCapable": True, "holdManual": True})
    assert hold["lfTx"] is False
    assert "holdManual" in hold["reasons"]

    assert md.lf_capability({"lfArmed": True, "band": "10-20"})["lfTx"] is True
    assert md.lf_capability({"lfArmed": True})["lfTx"] is False

    assert cap["micBinHz"] == pytest.approx(23.44, abs=0.01)
    assert cap["txBinHz"] == pytest.approx(2.93, abs=0.01)
    assert cap["lfBandHz"] == [10.0, 20.0]

    fixtures = [
        None,
        {},
        {"lfDriveCapable": True},
        {"lfDriveCapable": True, "holdManual": True},
        {"lfArmed": True, "band": "10-20"},
        {"lfArmed": True},
        {"lfArmed": True, "band": "lf", "lfDriveCapable": False},
    ]
    for t in fixtures:
        out = md.lf_capability(t)
        assert out["lfTx"] is priors.lf_drive_capable(t)
        assert out["lfMic"] is False
        lf_mic_reasons = [r for r in out["reasons"] if r.startswith("lfMic")]
        assert len(lf_mic_reasons) >= 2
        assert any("high-pass" in r for r in lf_mic_reasons)
        assert any("23.44 Hz/bin" in r for r in lf_mic_reasons)
        assert any("proxy" in r for r in lf_mic_reasons)


# ── MD-14 hw_limits_report keys ──────────────────────────────────────────────


def test_md14_hw_limits_report():
    r = md.hw_limits_report()
    assert r["issue"] == 25
    assert r["status"] == "hw-limited"
    assert r["blocksRedeploy"] is False
    assert r["nativeCompanionIssue"] == 9
    assert [limit["id"] for limit in r["limits"]] == ["full_aec", "lf_mic", "lf_tx", "alpha_calibration"]
    for limit in r["limits"]:
        assert set(limit) == {"id", "title", "limitedBy", "shippedPath", "doc", "nativePath"}
        assert all(isinstance(v, str) and v for v in limit.values())
    assert "docs/algorithms.md" in r["docs"]
    assert "docs/iphone-bluetooth.md" in r["docs"]
    dumped = json.dumps(r)
    assert json.loads(dumped) == r
    assert "http" not in dumped
    again = md.hw_limits_report()
    assert again == r and again is not r
    assert again["limits"][0] is not r["limits"][0]
    # Pointers the brief requires: docs + native companion path (#9).
    assert any("#9" in limit["nativePath"] for limit in r["limits"])
    assert r["limits"][0]["doc"] == "docs/iphone-bluetooth.md"
    assert r["limits"][1]["doc"].startswith("docs/algorithms.md")


# ── MD-15 honesty greps + import hygiene ─────────────────────────────────────


def test_md15_honesty_source_greps():
    src = (PKG_DIR / "iot_asp_autoroute" / "mic_diff.py").read_text(encoding="utf-8")
    for forbidden in ("CFD", "Navier", "bluetooth.requestDevice", "import scipy", "from google", "os.environ"):
        assert forbidden not in src, forbidden
    assert "proxy" in src


def test_md15_fresh_import_has_no_scipy_or_google():
    code = (
        "import sys\n"
        "import iot_asp_autoroute\n"  # package __init__ may soft-import agent when ADK is installed
        "before = set(sys.modules)\n"
        "import iot_asp_autoroute.mic_diff\n"
        "new = set(sys.modules) - before\n"
        "bad = sorted(m for m in new if m.split('.')[0] in ('scipy', 'google'))\n"
        "assert not bad, bad\n"
        "print('ok')\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(PKG_DIR),
        capture_output=True,
        text=True,
        env={**os.environ, "IOT_ASP_AUTOROUTE_DRY_RUN": "1"},
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "ok"


# ── MD-16 CLI demo ───────────────────────────────────────────────────────────


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "iot_asp_autoroute.mic_diff", *args],
        cwd=str(PKG_DIR),
        capture_output=True,
        text=True,
        env={**os.environ, "IOT_ASP_AUTOROUTE_DRY_RUN": "1"},
    )


def test_md16_cli_demo():
    first = _run_cli("--demo")
    assert first.returncode == 0, first.stderr
    out = json.loads(first.stdout)
    assert set(out) == {"micDiff", "calibration", "burst", "burstHold", "aec", "lf", "report"}
    assert out["micDiff"] == 5.5
    assert out["calibration"]["ok"] is True
    assert abs(out["calibration"]["alpha"] - 0.85) < 0.1
    assert out["burst"]["extreme"] is True
    assert out["burst"]["quietExtreme"] is False
    assert out["burstHold"]["reason"] == "holdManual — refuse"
    assert out["aec"]["fullAEC"] is False
    assert out["lf"]["lfMic"] is False
    assert len(out["report"]["limits"]) == 4

    second = _run_cli("--demo")
    assert second.stdout == first.stdout  # byte-identical: seeded, no timestamps

    usage = _run_cli()
    assert usage.returncode == 2
    assert usage.stdout == ""
    assert "usage" in usage.stderr.lower()


def test_md16_demo_function_matches_cli():
    assert md.demo() == md.demo()
    assert json.loads(_run_cli("--demo").stdout) == json.loads(json.dumps(md.demo()))


# ── MD-17 negative controls ──────────────────────────────────────────────────


def test_md17_negative_controls():
    assert md.burst_decision("6.5")["extreme"] is True
    assert md.burst_decision("abc")["reason"] == "micDiff unavailable"
    assert md.burst_decision(True)["reason"] == "micDiff unavailable"  # bool is not a level

    bogus = md.apply_burst_bias(BASE_PATCH, {"extreme": True, "shriekMsBias": 999, "micDiffDb": 9})
    assert bogus["shriekMs"] == 120.0
    assert bogus["burstBias"]["shriekMsBias"] == 15
    assert clamps.validate_patch(bogus)[0] is True

    assert md.apply_burst_bias({"algo": "hop"}, {}) == {"algo": "hop"}
    assert md.apply_burst_bias({"algo": "hop"}, None) == {"algo": "hop"}

    assert md.lf_capability({"lfDriveCapable": "true"})["lfTx"] is False
    assert priors.lf_drive_capable({"lfDriveCapable": "true"}) is False

    # Unknown telemetry keys are ignored, never echoed.
    d = md.burst_decision_from_telemetry({"micDiff": 9, "bogusKey": "x", "vibClass": "physical"})
    assert d["extreme"] is True and "bogusKey" not in json.dumps(d)


# ── MD-18 refuse, never rewrite, an out-of-policy base patch ─────────────────


def test_md18_apply_burst_bias_refuses_out_of_policy_base():
    """CLAUDE.md invariant 5: the bias must never launder a patch validate_patch refuses."""
    d = _extreme_decision(9.0)
    bad_patches = [
        {"algo": "hop", "shriekMs": 500},
        {"algo": "hop", "shriekMs": -100},
        {"algo": "hop", "shriekMs": 0},
        {"algo": "hop", "shriekMs": "abc"},
        {"algo": "evil", "shriekMs": 50},
        {"algo": "hop", "fMin": 22000, "fMax": 18000, "shriekMs": 50},
        {"algo": "hop", "pulseMs": 5000, "shriekMs": 50},
        {"algo": "hop", "vol": 101, "shriekMs": 50},
    ]
    for patch in bad_patches:
        ok_in, msg_in, _ = clamps.validate_patch(patch)
        assert ok_in is False, patch  # precondition: validate_patch refuses the input
        snapshot = copy.deepcopy(patch)
        out = md.apply_burst_bias(patch, d)
        assert out == snapshot, patch  # untouched copy: no algo swap, no shriekMs rewrite
        assert out is not patch and patch == snapshot
        assert "burstBias" not in out and out.get("algo") == patch.get("algo")
        ok_out, msg_out, _ = clamps.validate_patch(out)
        assert ok_out is False and msg_out == msg_in, patch  # downstream refusal is unchanged
        eligible, reason = md.burst_bias_eligibility(patch)
        assert eligible is False
        assert reason == f"{md.BIAS_REFUSE_PREFIX}{msg_in}"

    # Eligible boundaries: only the +15 delta is clamped, the input is never rewritten.
    assert md.apply_burst_bias({"algo": "hop", "shriekMs": 20}, d)["shriekMs"] == 35.0
    assert md.apply_burst_bias({"algo": "hop", "shriekMs": 105}, d)["shriekMs"] == 120.0
    assert md.apply_burst_bias({"algo": "hop", "shriekMs": 120}, d)["shriekMs"] == 120.0
    assert md.apply_burst_bias({"algo": "hop", "shriekMs": None}, d)["shriekMs"] == 65.0
    assert md.burst_bias_eligibility(BASE_PATCH) == (True, "ok")
    assert md.burst_bias_eligibility("not-a-dict")[0] is False
    assert md.burst_bias_eligibility(None)[0] is False

    # Same guarantee through the integrated author: a quiet draft under a burst is biased,
    # a draft that validate_patch refuses is refused with validate_patch's message.
    from iot_asp_autoroute import sudden_freq as sf

    ok, msg, patch = sf.author_sudden_freq_patch({"deviceId": "n1", "algo": "hop", "shriekMs": 50, "micDiff": 9.0})
    assert ok is True and patch["algo"] == "shriek_chirp" and patch["shriekMs"] == 70.0 and "burstBias" in patch
    ok_h, msg_h, patch_h = sf.author_sudden_freq_patch({"deviceId": "n1", "holdManual": True, "micDiff": 40.0})
    assert ok_h is False and patch_h == {} and "holdManual" in msg_h


# ── MD-19 spec carries the mandatory sections in order ───────────────────────

SPEC_PATH = ROOT / "docs" / "specs" / "25-hw-limited-lf-aec-micdiff.md"
REQUIRED_SECTIONS = [
    "Status",
    "Goal",
    "Prior art",
    "Shipped on `main`",
    "Remaining scope",
    "Wire fields",
    "Clamps / safety",
    "Acceptance tests",
    "CI gate",
    "Risks / HW limits",
    "Sources",
]


def test_md19_spec_sections_and_prior_art():
    text = SPEC_PATH.read_text(encoding="utf-8")
    headings = [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]
    assert headings == REQUIRED_SECTIONS, headings  # .claude/rules/docs-and-specs.md order
    prior = text.split("## Prior art", 1)[1].split("## Shipped on `main`", 1)[0]
    for venue in ("this repo", "mac clone", "org repos", "awesome-list", "context7", "firecrawl"):
        assert venue in prior.lower(), venue
    # The register row and the in-repo sibling helper are both cited.
    assert "docs/PRIOR_ART.md" in prior and "features_live.py" in prior
    # The spec documents the refuse-never-rewrite contract of apply_burst_bias.
    assert "burst_bias_eligibility" in text and "MD-18" in text and "MD-19" in text
