"""Tests for iot_asp_autoroute.fleet_log (#22) — offline, deterministic, stdlib-only module.

Run: python3 -m pytest tests/test_fleet_log.py -q
"""

from __future__ import annotations

import copy
import json
import os
import random
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = ROOT / "services" / "autoroute-adk"
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from iot_asp_autoroute import fleet_log  # noqa: E402
from iot_asp_autoroute.fleet_log import (  # noqa: E402
    RECORD_KEYS,
    aggregate_records,
    demo_fixture,
    emit_log,
    enrich_telemetry,
    infer_band,
    log_record,
    night_ny,
    read_log_records,
    retention_plan,
    safe_node,
    safe_ts,
    scrub_pii,
    write_log_record,
)

EXPECTED_KEYS = [
    "kind", "schemaVersion", "ts", "level", "event", "deviceId", "band", "power", "nightNY",
    "lfArmed", "lfDriveCapable", "lfGate", "algo", "vibClass", "suddenFreq", "suddenState",
    "holdManual", "peakHz", "absA", "micEnergy", "impulse", "volBlast", "alarmState", "msg",
]  # fmt: skip

BASE_TEL = {
    "schemaVersion": 1,
    "deviceId": "node1",
    "ts": "2026-01-15T12:00:00Z",
    "algo": "pulse",
    "peakHz": 19500,
    "suddenFreq": True,
    "suddenState": "rotate",
    "absA": 0.12,
    "micEnergy": 0.03,
    "fMin": 17000,
    "fMax": 23000,
    "vibClass": "physical",
    "holdManual": False,
}


@pytest.fixture
def dry_root(tmp_path, monkeypatch):
    monkeypatch.setenv("IOT_ASP_AUTOROUTE_DRY_RUN", "1")
    monkeypatch.setenv("IOT_ASP_AUTOROUTE_DRY_ROOT", str(tmp_path))
    return tmp_path


# 1. enrich determinism / purity
def test_enrich_is_pure_and_idempotent():
    t = copy.deepcopy(BASE_TEL)
    t["suddenFreqMeta"] = {"flux": 12.4}
    snapshot = copy.deepcopy(t)
    a = enrich_telemetry(t)
    b = enrich_telemetry(t)
    assert a == b
    assert t == snapshot
    assert enrich_telemetry(a) == a
    assert a is not t and a["suddenFreqMeta"] is not t["suddenFreqMeta"]


# 2. nightNY boundaries — EST (UTC−5)
@pytest.mark.parametrize(
    "ts,expected",
    [
        ("2026-01-16T02:59:59Z", False),  # NY 21:59:59
        ("2026-01-16T03:00:00Z", True),  # NY 22:00:00
        ("2026-01-15T11:59:59Z", True),  # NY 06:59:59
        ("2026-01-15T12:00:00Z", False),  # NY 07:00:00
    ],
)
def test_night_ny_est_boundaries(ts, expected):
    assert night_ny(ts) is expected


# 3. nightNY boundaries — EDT (UTC−4)
@pytest.mark.parametrize(
    "ts,expected",
    [
        ("2026-07-16T01:59:59Z", False),
        ("2026-07-16T02:00:00Z", True),
        ("2026-07-15T10:59:59Z", True),
        ("2026-07-15T11:00:00Z", False),
    ],
)
def test_night_ny_edt_boundaries(ts, expected):
    assert night_ny(ts) is expected


# 4. ts forms
def test_night_ny_ts_forms():
    assert night_ny(1768478400000) is False  # 2026-01-15T12:00:00Z (epoch ms)
    assert night_ny(1768478399000) is True
    assert night_ny(1768478399) is True  # epoch s
    assert night_ny(None) is False
    assert night_ny("garbage") is False
    assert night_ny("2026-01-15T11-59-59Z") is True  # filename form from tools.py
    assert night_ny("2026-01-15T06:59:59-05:00") is True  # explicit offset
    assert enrich_telemetry({"deviceId": "node1"})["nightNY"] is False  # missing ts
    assert fleet_log.parse_ts("2026-01-15T11:59:59Z").isoformat() == "2026-01-15T11:59:59+00:00"


# 5. band inference
@pytest.mark.parametrize(
    "t,expected",
    [
        ({}, "17-23k"),
        ({"band": "10-20"}, "10-20"),
        ({"band": "lf"}, "10-20"),
        ({"fMin": 15}, "10-20"),
        ({"fMin": 17000}, "17-23k"),
        ({"band": "bogus", "fMin": 17000}, "17-23k"),
        ({"band": "17-23k", "fMin": 15}, "17-23k"),
    ],
)
def test_band_inference(t, expected):
    assert infer_band(t) == expected
    assert enrich_telemetry(t)["band"] == expected


# 6. defaults
def test_enrich_defaults():
    e = enrich_telemetry({"deviceId": "node1", "ts": "2026-01-15T12:00:00Z"})
    assert e["power"] == "ac120"
    assert e["lfArmed"] is False
    assert e["lfDriveCapable"] is False
    assert e["lfGate"] is False
    assert e["vibClass"] == "none"
    assert e["band"] == "17-23k"
    assert "piiDropped" not in e
    assert enrich_telemetry({"power": "battery"})["power"] == "battery"


# 7. lfGate truth table + bool coercion
@pytest.mark.parametrize("armed", [True, False])
@pytest.mark.parametrize("capable", [True, False])
@pytest.mark.parametrize("vib", ["infra_felt", "physical"])
def test_lf_gate_truth_table(armed, capable, vib):
    e = enrich_telemetry({"lfArmed": armed, "lfDriveCapable": capable, "vibClass": vib})
    assert e["lfGate"] is (armed and capable and vib == "infra_felt")


def test_lf_bool_coercion():
    assert enrich_telemetry({"lfArmed": 1})["lfArmed"] is True
    assert enrich_telemetry({"lfArmed": "yes"})["lfArmed"] is True
    assert enrich_telemetry({"lfArmed": None})["lfArmed"] is False
    assert enrich_telemetry({"lfArmed": "false"})["lfArmed"] is False
    assert enrich_telemetry({"lfDriveCapable": "0"})["lfDriveCapable"] is False


# 8. PII scrub
PII_INPUT_KEYS = [
    "streetAddress", "name", "contactEmail", "phone", "lat", "lon", "gpsFix", "clientIp",
    "transcript", "speechText", "recordingUri", "latitude",
]  # fmt: skip
# Lowercase compound spellings (no separator) — must drop via substring / compound-token match.
PII_COMPOUND_KEYS = [
    "emailaddress", "username", "address1", "address2", "phonenumber", "streetaddress",
    "homeaddress", "ipaddress", "ipaddr", "emailaddr", "fullname", "gpslat", "latlon", "latlng",
    "gpscoords", "speechtext", "transcription", "recordingurl", "telephone", "cellphone",
    "geolocation", "location", "zipcode", "postalcode",
]  # fmt: skip
# Look-alikes that carry no PII and must survive (audio route / timing keys are plausible telemetry).
PII_LOOKALIKE_KEYS = [
    "headphones", "headphoneConnected", "microphoneGain", "earphoneRoute", "latency", "long",
    "ipc", "filename", "elapsed", "gain", "geminiAutorouteFlag", "records", "recordCount",
]  # fmt: skip


def test_pii_scrub_drops_keys_and_keeps_contract():
    from iot_asp_autoroute import colab_etl  # imports numpy via vib_anomaly; local to this test

    fixture = colab_etl.sample_telemetry_fixture()
    t = dict(fixture)
    for k in PII_INPUT_KEYS:
        t[k] = "SENTINEL_PII"
    t["meta"] = {"homeAddress": "SENTINEL_PII", "keep": 1}
    t["logTail"] = [{"seq": 1, "msg": "ok", "userName": "SENTINEL_PII"}]

    clean, dropped = scrub_pii(t)
    assert len(dropped) == 14 and dropped == sorted(dropped)
    assert "SENTINEL_PII" not in json.dumps(clean)
    assert clean["meta"] == {"keep": 1}
    assert clean["logTail"] == [{"seq": 1, "msg": "ok"}]

    enriched = enrich_telemetry(t)
    for k in PII_INPUT_KEYS:
        assert k not in enriched
    assert "homeAddress" not in json.dumps(enriched)
    assert enriched["piiDropped"] == 14
    for k, v in fixture.items():
        if k in ("nightNY",):  # always recomputed server-side from ts
            continue
        assert enriched[k] == v, k
    for k in colab_etl.TELEMETRY_FEATURE_COLUMNS:
        assert not fleet_log.is_pii_key(k), k
    assert "SENTINEL_PII" not in json.dumps(enriched)
    rec = log_record("info", "ingest", enriched, msg=f"dropped={dropped}")
    assert "SENTINEL_PII" not in json.dumps(rec)


def test_pii_scrub_compound_lowercase_keys():
    """Regression: keys that merely *contain* a deny word without a separator must drop too."""
    for k in PII_COMPOUND_KEYS:
        assert fleet_log.is_pii_key(k), k
        assert fleet_log.is_pii_key(k.upper()), k
    for k in PII_LOOKALIKE_KEYS:
        assert not fleet_log.is_pii_key(k), k
    t = {k: "LEAK" for k in PII_COMPOUND_KEYS}
    t.update({"ts": "2026-01-15T12:00:00Z", "deviceId": "node1", "headphones": True})
    clean, dropped = scrub_pii(t)
    assert dropped == sorted(PII_COMPOUND_KEYS)
    assert "LEAK" not in json.dumps(clean)
    assert clean["headphones"] is True and clean["ts"] == "2026-01-15T12:00:00Z"
    enriched = enrich_telemetry(t)
    assert "LEAK" not in json.dumps(enriched)
    assert enriched["piiDropped"] == len(PII_COMPOUND_KEYS)
    assert "LEAK" not in json.dumps(log_record("info", "ingest", t))


def test_pii_scrub_api_contract_keys_survive():
    contract = [
        "band", "power", "nightNY", "lfArmed", "lfDriveCapable", "lastHopAgeMs", "ctxResumes",
        "watchdogTrips", "logSeq", "logTail", "ax", "ay", "az", "gx", "gy", "gz", "accelAxes",
        "gyroAxes", "outLevel", "micDiff", "bandBurst", "soundBurst", "extremeActive", "lfEnergy",
        "usEnergy", "materialPreset", "engineId", "deviceId", "peakHz", "suddenFreqMeta",
    ]  # fmt: skip
    for k in contract:
        assert not fleet_log.is_pii_key(k), k
    assert fleet_log.is_pii_key("IPAddress")
    assert fleet_log.is_pii_key("recording_uri")
    assert fleet_log.is_pii_key("longitude")


# 9. record key order
def test_record_key_order_and_validation():
    rec = log_record("info", "ingest", BASE_TEL)
    assert list(rec.keys()) == RECORD_KEYS == EXPECTED_KEYS
    assert rec["kind"] == "fleet_log"
    assert rec["schemaVersion"] == 1
    assert rec["ts"] == "2026-01-15T12:00:00Z"
    assert rec["algo"] == "am_gate"  # UI alias mapped to wire name
    assert rec["suddenFreq"] is True and rec["suddenState"] == "rotate"
    assert rec["peakHz"] == 19500 and rec["absA"] == 0.12 and rec["micEnergy"] == 0.03
    with pytest.raises(ValueError):
        log_record("fatal", "ingest", BASE_TEL)
    long = log_record("info", "ingest", BASE_TEL, msg="x" * 1000)
    assert len(long["msg"]) == 240
    assert log_record("INFO", "ingest", BASE_TEL)["level"] == "info"
    fallback = log_record("debug", "x", {"a": 0.5}, now=fleet_log.parse_ts("2026-02-01T00:00:00Z"))
    assert fallback["absA"] == 0.5 and fallback["ts"] == "2026-02-01T00:00:00Z"
    assert fallback["deviceId"] == "node1" and fallback["peakHz"] is None


# 10. JSONL round-trip
def test_jsonl_round_trip(dry_root):
    records = demo_fixture()
    for r in records:
        res = write_log_record("node1", r)
        assert res["ok"], res
        assert res["uri"].startswith("file://") and res["mode"] == "append"
        assert res["path"] == "meta/logs/node1/2026-01-15.jsonl"
    f = dry_root / "meta" / "logs" / "node1" / "2026-01-15.jsonl"
    assert f.is_file()
    lines = f.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 12
    for line in lines:
        json.loads(line)
    assert list(json.loads(lines[0], object_pairs_hook=OrderedDict)) == RECORD_KEYS
    assert read_log_records("node1", "2026-01-15") == records
    assert read_log_records("node1") == records
    assert read_log_records("node9") == []
    with f.open("a", encoding="utf-8") as fh:
        fh.write("{not json\n")
    assert len(read_log_records("node1", "2026-01-15")) == 12
    recs, skipped = fleet_log.read_log_records_with_stats("node1")
    assert len(recs) == 12 and skipped == 1
    assert not (ROOT / ".autoroute-dry" / "meta" / "logs" / "node1" / "2026-01-15.jsonl").exists()
    assert write_log_record("../evil", records[0])["path"].startswith("meta/logs/_evil/")


def test_write_log_record_never_raises(dry_root, monkeypatch):
    monkeypatch.setenv("IOT_ASP_AUTOROUTE_DRY_ROOT", str(dry_root / "file-not-dir"))
    (dry_root / "file-not-dir").write_text("x", encoding="utf-8")
    res = write_log_record("node1", demo_fixture()[0])
    assert res["ok"] is False and "error" in res


def test_jsonl_unicode_line_separators_round_trip(dry_root):
    """Regression: U+2028 / U+2029 / U+0085 in a string field must not shatter the JSONL line.

    ``str.splitlines()`` treats those code points as line breaks; the writer \\u-escapes them
    (``ensure_ascii=True``) and the reader splits on ``\\n`` only, so the record survives intact.
    """
    weird = ["rot\u2028ate", "on\u2029set", "id\u0085le", "em\u2014dash \u00e9"]
    records = []
    for i, state in enumerate(weird):
        t = {**BASE_TEL, "ts": f"2026-01-15T12:00:0{i}Z", "suddenState": state, "deviceId": f"n\u2028{i}"}
        rec = log_record("info", "ingest", t, msg=state)
        assert rec["suddenState"] == state
        assert write_log_record("node1", rec)["ok"]
        records.append(rec)
    f = dry_root / "meta" / "logs" / "node1" / "2026-01-15.jsonl"
    raw = f.read_bytes()
    assert raw.isascii(), "records must be \\u-escaped so one record == one \\n line"
    assert raw.count(b"\n") == 4 and raw.endswith(b"\n")
    assert len(raw.decode("utf-8").splitlines()) == 4  # nothing left for splitlines() to split on
    got, skipped = fleet_log.read_log_records_with_stats("node1", "2026-01-15")
    assert skipped == 0 and got == records
    assert [r["suddenState"] for r in got] == weird
    # reader tolerates CRLF and a raw (legacy, unescaped) separator inside a JSON string
    legacy = '{"kind":"fleet_log","suddenState":"a\u2028b"}\r\n{"kind":"fleet_log","x":1}\n'
    recs, bad = fleet_log._parse_lines(legacy)
    assert bad == 0 and [r.get("suddenState", r.get("x")) for r in recs] == ["a\u2028b", 1]


# 11. aggregate math
def test_aggregate_math():
    records = demo_fixture()
    agg = aggregate_records(records, window_s=300)
    assert list(agg) == [
        "node", "first_ts", "last_ts", "count", "sudden_count", "hold_fraction", "night_fraction",
        "by_algo", "by_vibClass", "by_band", "by_level", "windows",
    ]  # fmt: skip
    assert agg["node"] == "node1"
    assert agg["count"] == 12
    assert agg["first_ts"] == "2026-01-15T11:55:00Z"
    assert agg["last_ts"] == "2026-01-15T12:06:00Z"
    assert agg["sudden_count"] == 3
    assert agg["hold_fraction"] == 0.25
    assert agg["night_fraction"] == round(5 / 12, 4) == 0.4167
    assert agg["by_algo"] == {"am_gate": 4, "burst": 4, "hop": 4}
    assert agg["by_vibClass"] == {"acoustic": 3, "infra_felt": 3, "none": 3, "physical": 3}
    assert agg["by_band"] == {"10-20": 2, "17-23k": 10}
    assert agg["by_level"] == {"info": 9, "warn": 3}
    assert agg["windows"] == [
        {"start": "2026-01-15T11:55:00Z", "end": "2026-01-15T12:00:00Z", "count": 5, "sudden": 2},
        {"start": "2026-01-15T12:00:00Z", "end": "2026-01-15T12:05:00Z", "count": 5, "sudden": 1},
        {"start": "2026-01-15T12:05:00Z", "end": "2026-01-15T12:10:00Z", "count": 2, "sudden": 0},
    ]
    shuffled = list(records)
    random.Random(42).shuffle(shuffled)
    assert aggregate_records(shuffled, window_s=300) == agg
    empty = aggregate_records([])
    assert empty["count"] == 0 and empty["hold_fraction"] == 0.0 and empty["night_fraction"] == 0.0
    assert empty["first_ts"] is None and empty["windows"] == [] and empty["node"] is None
    assert aggregate_records([], node="node2")["node"] == "node2"
    with pytest.raises(ValueError):
        aggregate_records(records, window_s=0)
    unknown = aggregate_records([{"ts": "bogus", "algo": None}])
    assert unknown["count"] == 1 and unknown["by_algo"] == {"unknown": 1} and unknown["windows"] == []


# 12. retention_plan
def test_retention_plan():
    plan = retention_plan()
    assert plan["raw"]["prefix"] == "meta/logs/" and plan["raw"]["days"] == 30
    assert plan["aggregates"]["prefix"] == "meta/logs-agg/" and plan["aggregates"]["days"] == 365
    assert plan["features"]["prefix"] == "meta/features/"
    assert "meta/patches/" not in json.dumps(plan).replace("never meta/patches/", "")
    rules = plan["lifecycle"]["rule"]
    assert len(rules) == 2 and all(r["action"] == {"type": "Delete"} for r in rules)
    assert rules[0]["condition"] == {"age": 30, "matchesPrefix": ["meta/logs/"]}
    assert rules[1]["condition"] == {"age": 365, "matchesPrefix": ["meta/logs-agg/"]}
    assert json.dumps(plan) == json.dumps(retention_plan())


# 13. CLI demo
def test_cli_demo(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith("IOT_ASP_")}
    env["IOT_ASP_AUTOROUTE_DRY_ROOT"] = str(tmp_path)
    env.pop("PYTHONPATH", None)
    proc = subprocess.run(
        [sys.executable, "-m", "iot_asp_autoroute.fleet_log", "--demo"],
        cwd=str(PKG_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["sample"]["kind"] == "fleet_log"
    assert list(out["sample"]) == RECORD_KEYS
    assert out["aggregate"]["count"] == 12
    assert out["written"] == 12
    assert (tmp_path / "meta" / "logs" / "node1" / "2026-01-15.jsonl").is_file()
    low = proc.stdout.lower()
    for tok in sorted(fleet_log.PII_DENY_TOKENS | fleet_log.PII_DENY_EXACT | set(fleet_log.PII_DENY_SUBSTRINGS)):
        assert f'"{tok}"' not in low, tok
    usage = subprocess.run(
        [sys.executable, "-m", "iot_asp_autoroute.fleet_log"],
        cwd=str(PKG_ROOT), env=env, capture_output=True, text=True, timeout=60,
    )
    assert usage.returncode == 2


# 14. import hygiene (fresh subprocess)
def test_import_hygiene():
    code = (
        "import sys, iot_asp_autoroute.fleet_log as f;"
        "adk = 'iot_asp_autoroute.agent' in sys.modules and sys.modules['iot_asp_autoroute.agent'] is not None;"
        "assert 'google.cloud.storage' not in sys.modules;"
        "assert adk or 'numpy' not in sys.modules, 'numpy';"
        "assert adk or 'scipy' not in sys.modules, 'scipy';"
        "assert f.RECORD_KEYS[0] == 'kind'; print('ok')"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code], cwd=str(PKG_ROOT), capture_output=True, text=True, timeout=60,
        env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"},
    )
    assert proc.returncode == 0, proc.stderr
    src = (PKG_ROOT / "iot_asp_autoroute" / "fleet_log.py").read_text(encoding="utf-8")
    assert "import numpy" not in src and "import scipy" not in src
    for line in src.splitlines():
        assert not line.startswith("from google.cloud"), line


# 15. negative controls
def test_negative_controls():
    held = enrich_telemetry({**BASE_TEL, "holdManual": True})
    assert held["holdManual"] is True
    rec = log_record("warn", "hold_refuse", held)
    assert rec["holdManual"] is True and rec["suddenFreq"] is True  # phone flag preserved, hold logged
    odd = enrich_telemetry({**BASE_TEL, "__proto__": {"x": 1}, "priors": ["bogus"]})
    assert odd["__proto__"] == {"x": 1} and odd["priors"] == ["bogus"]
    assert log_record("info", "ingest", {**BASE_TEL, "algo": "bogus_algo"})["algo"] == "bogus_algo"
    assert log_record("info", "ingest", {**BASE_TEL, "vibClass": "weird"})["vibClass"] == "none"
    assert log_record("info", "ingest", {**BASE_TEL, "peakHz": "nan"})["peakHz"] is None


# 16. malformed phone values never raise (ingest calls enrich before any write)
@pytest.mark.parametrize("vib", [5, ["x"], {"a": 1}, 1.5, True, None, b"physical"])
def test_enrich_non_string_vib_class_never_raises(vib):
    e = enrich_telemetry({**BASE_TEL, "vibClass": vib})
    assert e["vibClass"] == "none" and e["lfGate"] is False
    rec = log_record("info", "ingest", {**BASE_TEL, "vibClass": vib})
    assert rec["vibClass"] == "none" and list(rec) == RECORD_KEYS


def test_enrich_non_string_power_and_band_never_raise():
    e = enrich_telemetry({**BASE_TEL, "power": {"v": 120}, "band": ["10-20"], "fMin": ["x"]})
    assert e["power"] == "ac120" and e["band"] == "17-23k"
    assert enrich_telemetry({"power": "  battery "})["power"] == "battery"
    assert enrich_telemetry({"power": "   "})["power"] == "ac120"
    assert enrich_telemetry({"power": 0})["power"] == "ac120"


def test_emit_log_never_raises(dry_root):
    tel = {**BASE_TEL, "vibClass": 5, "power": None, "algo": None}
    res = emit_log("node1", "info", "ingest", tel, msg="piiDropped=0")
    assert res["ok"] is True and res["path"] == "meta/logs/node1/2026-01-15.jsonl"
    got = read_log_records("node1", "2026-01-15")
    assert len(got) == 1 and got[0]["vibClass"] == "none" and got[0]["algo"] == "hop"
    bad = emit_log("node1", "fatal", "ingest", tel)  # invalid level → error dict, not ValueError
    assert bad["ok"] is False and "ValueError" in bad["error"] and bad["path"] is None
    assert emit_log("node1", "info", "ingest", "not-a-dict")["ok"] is True  # non-dict → defaults
    assert len(read_log_records("node1")) == 2


# 17. object-name safety helpers shared with tools.ingest_telemetry
@pytest.mark.parametrize(
    "node,expected",
    [
        ("node1", "node1"),
        ("..", "node1"),
        (".", "node1"),
        ("", "node1"),
        (None, "node1"),
        ("../patches", "_patches"),
        ("../../patches/node1", "_.._patches_node1"),  # no '/', not a '.'/'..' segment
        ("a/b", "a_b"),
        ("node one", "node_one"),
        ("..hidden", "hidden"),
        ("n.1", "n.1"),
    ],
)
def test_safe_node(node, expected):
    assert safe_node(node) == expected
    assert "/" not in safe_node(node) and safe_node(node) not in (".", "..")
    assert fleet_log.record_path(node, "2026-01-15T12:00:00Z") == f"meta/logs/{expected}/2026-01-15.jsonl"


def test_safe_ts_normalises_any_wire_ts():
    now = fleet_log.parse_ts("2026-02-01T00:00:00Z")
    assert safe_ts("2026-01-15T12:00:00Z") == "2026-01-15T12-00-00Z"
    assert safe_ts(1768478400000) == "2026-01-15T12-00-00Z"
    assert safe_ts("2026-01-15T07:00:00-05:00") == "2026-01-15T12-00-00Z"
    for evil in ("../../patches/node1", "..", "", None, "garbage", {"x": 1}):
        assert safe_ts(evil, now=now) == "2026-02-01T00-00-00Z", evil
    assert ":" not in safe_ts("2026-01-15T12:00:00Z") and "/" not in safe_ts("a/b", now=now)
