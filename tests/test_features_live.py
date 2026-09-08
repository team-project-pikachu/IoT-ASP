"""Tests for iot_asp_autoroute.features_live (#26) — offline, deterministic.

Acceptance IDs FL-01 … FL-16 from docs/specs/26-colab-live-gcs-features.md.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = ROOT / "services" / "autoroute-adk"
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from iot_asp_autoroute import features_live as fl  # noqa: E402
from iot_asp_autoroute import gcs_io  # noqa: E402
from iot_asp_autoroute.colab_etl import TELEMETRY_FEATURE_COLUMNS  # noqa: E402

NB_IPYNB = ROOT / "notebooks" / "iot_asp_colab_etl.ipynb"
NB_MD = ROOT / "notebooks" / "iot_asp_colab_etl.md"


@pytest.fixture
def dry_root(tmp_path, monkeypatch):
    """Dry-run mirror under tmp_path; LIVE_GCS / bucket unset."""
    monkeypatch.setenv("IOT_ASP_AUTOROUTE_DRY_ROOT", str(tmp_path))
    monkeypatch.setenv("IOT_ASP_AUTOROUTE_DRY_RUN", "1")
    monkeypatch.delenv("LIVE_GCS", raising=False)
    monkeypatch.delenv("IOT_ASP_GCS_BUCKET", raising=False)
    monkeypatch.setattr(gcs_io, "DRY_RUN", True)
    monkeypatch.setattr(gcs_io, "DRY_ROOT", tmp_path)
    monkeypatch.setattr(gcs_io, "BUCKET", "")
    return tmp_path


# ── FL-01 micDiff ────────────────────────────────────────────────────────────


def test_fl01_mic_diff_math_and_passthrough():
    assert fl.mic_diff(-40.0, -30.0) == pytest.approx(-14.5)
    assert fl.mic_diff(-40.0, -30.0, given=3.25) == 3.25
    assert fl.mic_diff(-40.0, -30.0, given="nope") == pytest.approx(-14.5)
    assert fl.mic_diff(None, None) == 0.0
    assert fl.mic_diff("x", -30.0) == pytest.approx(25.5)
    assert fl.mic_diff(-40.0, -30.0, alpha=1.0) == pytest.approx(-10.0)
    assert fl.MIC_DIFF_ALPHA == 0.85


# ── FL-02 bandBurst ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "lf,us,expected",
    [
        (-50, -50, "both"),
        (-50, -70, "lf"),
        (-70, -50, "us"),
        (-70, -70, None),
        (None, None, None),
        ("bad", -50, "us"),
        (-60.0, -55.0, "both"),  # thresholds inclusive
    ],
)
def test_fl02_band_burst(lf, us, expected):
    assert fl.band_burst(lf, us) == expected


# ── FL-03 projection ─────────────────────────────────────────────────────────


def test_fl03_project_sensor_features():
    t = {
        "ax": "0.1",
        "ay": 0.2,
        "az": 0.3,
        "gyroAxes": [1.0, 2.0],  # wrong length → dropped
        "gx": 0.5,
        "outLevel": -30,
        "micDiff": None,  # None skipped
        "bandBurst": "nope",  # not allowed → dropped
        "soundBurst": "true",
        "extremeActive": 0,
        "lastHopAgeMs": 412.6,
        "ctxResumes": "2",
        "lfEnergy": float("nan"),  # non-finite → dropped
        "unknownKey": 1,
        "deviceId": "node1",
    }
    s = fl.project_sensor_features(t)
    assert s["accelAxes"] == [0.1, 0.2, 0.3]
    assert s["ax"] == 0.1 and isinstance(s["ax"], float)
    assert "gyroAxes" not in s
    assert "bandBurst" not in s
    assert "micDiff" not in s
    assert "lfEnergy" not in s
    assert "unknownKey" not in s and "deviceId" not in s
    assert s["soundBurst"] is True and s["extremeActive"] is False
    assert s["lastHopAgeMs"] == 413 and s["ctxResumes"] == 2
    assert s["outLevel"] == -30.0

    given = fl.project_sensor_features({"accelAxes": ("1", 2, 3.5), "bandBurst": "LF"})
    assert given["accelAxes"] == [1.0, 2.0, 3.5]
    assert given["bandBurst"] == "lf"
    assert set(s) <= set(fl.SENSOR_COLUMNS)


# ── FL-04 parsing + ordering ─────────────────────────────────────────────────


def _write(root: Path, name: str, text: str) -> None:
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_fl04_parse_json_jsonl_ordering_and_limit(dry_root):
    node = "nodeX"
    pre = f"meta/telemetry/{node}/"
    lines = [
        json.dumps({"deviceId": node, "ts": "2026-09-08T00:00:03Z", "absA": 0.03, "algo": "hop"}),
        "{not json",
        json.dumps({"deviceId": node, "ts": 1788825601000, "absA": 0.01}),  # epoch ms → :00:01
        "",
        json.dumps({"deviceId": node, "ts": "2026-09-08T00:00:02Z", "a": 0.02}),
    ]
    _write(dry_root, pre + "day.jsonl", "\n".join(lines) + "\n")
    _write(dry_root, pre + "2026-09-08T00-00-00Z.json", json.dumps({"deviceId": node, "ts": "2026-09-08T00:00:00Z", "absA": 0.0}))
    _write(dry_root, pre + "2026-09-08T00-00-04Z.json", json.dumps({"deviceId": node, "ts": "2026-09-08T00:00:04+00:00", "absA": 0.04}))

    names = fl.list_telemetry_names(node)
    assert pre + "day.jsonl" in names and len(names) == 3

    errors: list = []
    pts = fl.parse_telemetry_objects(names, errors=errors)
    assert [p["ts"] for p in pts] == [
        "2026-09-08T00:00:00Z",
        "2026-09-08T00:00:01Z",
        "2026-09-08T00:00:02Z",
        "2026-09-08T00:00:03Z",
        "2026-09-08T00:00:04Z",
    ]
    assert len(errors) == 1 and errors[0]["line"] == 1
    assert pts[2]["absA"] == 0.02  # alias a → absA via colab_etl.normalize_telemetry
    assert all(p["schemaVersion"] == 1 for p in pts)

    last2 = fl.latest_points(node, limit=2)
    assert [p["ts"] for p in last2] == ["2026-09-08T00:00:03Z", "2026-09-08T00:00:04Z"]
    assert fl.latest_points("ghost") == []


def test_normalize_ts_variants():
    assert fl.normalize_ts(1788825601000) == "2026-09-08T00:00:01Z"
    assert fl.normalize_ts(1788825601) == "2026-09-08T00:00:01Z"
    assert fl.normalize_ts("2026-09-08T00-00-05Z") == "2026-09-08T00:00:05Z"
    assert fl.normalize_ts("2026-09-08T01:00:05+01:00") == "2026-09-08T00:00:05Z"
    assert fl.normalize_ts(None) is None
    assert fl.normalize_ts("garbage") is None  # never echoes unparseable input
    assert fl.normalize_ts("zz/../../../patches/node1") is None
    assert fl.normalize_ts("2026-09-08T00:00:05Z") == "2026-09-08T00:00:05Z"


# ── FL-05 / FL-06 feature record + shriekBias ────────────────────────────────


def test_fl05_build_feature_record_demo():
    pts = fl.demo_points("node1", 12, 26)
    rec = fl.build_feature_record(pts, "node1")
    assert rec["kind"] == "iot_asp_features"
    assert rec["schemaVersion"] == 1
    assert rec["sourceCount"] == 12
    assert rec["anomaly"]["n"] == 12
    assert rec["anomaly"]["engine"] == "scipy"
    latest = pts[-1]
    assert rec["sensors"]["micDiff"] == pytest.approx(latest["micEnergy"] - 0.85 * latest["outLevel"])
    assert rec["sensors"]["bandBurst"] == "us"
    assert rec["sensors"]["accelAxes"] == [latest["ax"], latest["ay"], latest["az"]]
    assert rec["ts"] == latest["ts"]
    assert rec["live"] is False
    assert rec["writer"] == "iot_asp_autoroute.features_live"
    assert rec["sensorColumns"] == list(fl.SENSOR_COLUMNS)
    assert rec["micDiffAlpha"] == 0.85
    assert rec["telemetry"]["holdManual"] is False
    assert rec["shriekBias"] is False  # latest point (idx 11) has no burst
    # idx 9 carries soundBurst=True → bias when it is the latest
    rec9 = fl.build_feature_record(pts[:10], "node1")
    assert rec9["shriekBias"] is True and rec9["sourceCount"] == 10

    with pytest.raises(ValueError):
        fl.build_feature_record([], "node1")


def _one(**extra):
    base = {"deviceId": "node1", "ts": "2026-09-08T00:00:00Z", "algo": "hop", "absA": 0.02}
    base.update(extra)
    return base


@pytest.mark.parametrize(
    "extra,expected",
    [
        ({"soundBurst": True}, True),
        ({"extremeActive": True}, True),
        ({"micDiff": 6.5}, True),
        ({"micDiff": 5.9, "soundBurst": False, "extremeActive": False}, False),
        ({"micEnergy": -20.0, "outLevel": -32.0}, True),  # computed 7.2 dB
        ({"micEnergy": -40.0, "outLevel": -30.0}, False),  # computed -14.5 dB
        ({}, False),
    ],
)
def test_fl06_shriek_bias(extra, expected):
    rec = fl.build_feature_record([_one(**extra)], "node1")
    assert rec["shriekBias"] is expected
    if "micDiff" in extra:
        assert rec["sensors"]["micDiff"] == extra["micDiff"]  # phone value untouched


# ── FL-07 / FL-08 / FL-09 / FL-10 run_live + guard ───────────────────────────


def test_fl07_run_live_dry_run_writes_exactly_one_features_object(dry_root):
    seeded = fl._seed_demo("node1")
    assert len(seeded) == 12 and all(u.startswith("file://") for u in seeded)
    res = fl.run_live("node1", 50)
    assert res["ok"] is True
    assert res["live"] is False
    assert res["uri"].startswith("file://")
    assert res["sourceCount"] == 12
    assert res["object"].startswith("meta/features/node1/")
    feats = sorted((dry_root / "meta" / "features" / "node1").iterdir())
    assert len(feats) == 1
    assert feats[0].name.endswith(".json") and ":" not in feats[0].name
    assert feats[0].name == "2026-09-08T00-00-11Z.json"
    assert not (dry_root / "meta" / "patches").exists()
    body = json.loads(feats[0].read_text(encoding="utf-8"))
    assert body["kind"] == "iot_asp_features" and body["sourceCount"] == 12
    assert body["live"] is False
    assert "sensors" in body and body["sensors"]["micDiff"] == pytest.approx(-14.5)
    assert set(res["featureKeys"]) == set(body.keys())
    # gcs_io state restored
    assert gcs_io.DRY_RUN is True


def test_fl08_guard_refuses_patch_paths():
    with pytest.raises(ValueError, match="meta/patches"):
        fl.assert_not_patch_path("meta/patches/node1.json")
    with pytest.raises(ValueError):
        fl.assert_not_patch_path("/meta/patches/node1.json")
    fl.assert_not_patch_path("meta/features/node1/x.json")
    assert fl.features_object_name("node1", "2026-09-08T00:00:11Z") == "meta/features/node1/2026-09-08T00-00-11Z.json"
    assert fl.features_object_name("node1", 1788825601000) == "meta/features/node1/2026-09-08T00-00-01Z.json"


# ── FL-14 path-safe object names (node + ts) ─────────────────────────────────


@pytest.mark.parametrize(
    "bad",
    [
        "meta/features/node1/../../patches/node1.json",
        "meta/features/node1/zz/../../../patches/node1.json",
        "meta/features//node1/x.json",
        "meta/features/./x.json",
        "/meta/features/node1/x.json",
        "meta\\features\\node1\\x.json",
        "../patches/x.json",
    ],
)
def test_fl14_guard_refuses_unsafe_segments(bad):
    with pytest.raises(ValueError, match="refuse"):
        fl.assert_not_patch_path(bad)
    with pytest.raises(ValueError, match="refuse"):
        fl.assert_features_path(bad)


@pytest.mark.parametrize("node", ["../patches/x", "node1/../../patches", "a/b", "", " ", "node 1", ".", "..", "nöde", "node1\n", "node1\r"])
def test_fl14_node_validation(node, dry_root):
    with pytest.raises(ValueError, match="node id"):
        fl.validate_node(node)
    with pytest.raises(ValueError, match="node id"):
        fl.features_object_name(node, "2026-09-08T00:00:00Z")
    with pytest.raises(ValueError, match="node id"):
        fl.list_telemetry_names(node)
    with pytest.raises(ValueError, match="node id"):
        fl._seed_demo(node)
    with pytest.raises(ValueError, match="node id"):
        fl.run_live(node, 50)
    assert not (dry_root / "meta").exists()  # refused before any read or write
    assert fl.validate_node("node-1_A") == "node-1_A"


@pytest.mark.parametrize("ts", ["z/../../../patches/node1", "garbage", "", None, "2026-13-45", float("nan"), True, "day"])
def test_fl14_features_object_name_refuses_bad_ts(ts):
    with pytest.raises(ValueError, match="refuse"):
        fl.features_object_name("node1", ts)


def test_fl14_features_object_name_accepts_iso_variants():
    # date-only / offset / object-name forms are real ISO inputs → normalised, never refused
    assert fl.features_object_name("node1", "2026-09-08") == "meta/features/node1/2026-09-08T00-00-00Z.json"
    assert fl.features_object_name("node1", "2026-09-08T01:00:05+01:00") == "meta/features/node1/2026-09-08T00-00-05Z.json"
    assert fl.features_object_name("node1", "2026-09-08T00-00-05Z") == "meta/features/node1/2026-09-08T00-00-05Z.json"


def test_fl14_telemetry_controlled_ts_cannot_reach_patches(dry_root):
    """Phone-controlled ts with '..' is dropped; an existing patch object is untouched."""
    patch = dry_root / "meta" / "patches" / "node1.json"
    _write(dry_root, "meta/patches/node1.json", json.dumps({"schemaVersion": 1, "algo": "hop"}))
    before = patch.read_text(encoding="utf-8")
    pre = "meta/telemetry/node1/"
    lines = [
        json.dumps({"deviceId": "node1", "ts": "2026-09-08T00:00:09Z", "algo": "hop", "absA": 0.09, "soundBurst": True}),
        json.dumps({"deviceId": "node1", "ts": "zz/../../../patches/node1", "algo": "hop", "absA": 0.02}),
    ]
    _write(dry_root, pre + "day.jsonl", "\n".join(lines) + "\n")
    _write(dry_root, pre + "2026-09-08T00-00-01Z.json",
           json.dumps({"deviceId": "node1", "ts": "z/../../../patches/node1", "algo": "hop", "absA": 0.01}))

    errors: list = []
    pts = fl.parse_telemetry_objects(fl.list_telemetry_names("node1"), errors=errors)
    # .json object falls back to its (safe) name stem; the .jsonl line is dropped
    assert [p["ts"] for p in pts] == ["2026-09-08T00:00:01Z", "2026-09-08T00:00:09Z"]
    assert errors == [{"object": pre + "day.jsonl", "line": 1, "error": "unparseable ts"}]

    res = fl.run_live("node1", 50)
    assert res["ok"] is True and res["object"] == "meta/features/node1/2026-09-08T00-00-09Z.json"
    assert res["shriekBias"] is True
    assert (dry_root / "meta" / "features" / "node1" / "2026-09-08T00-00-09Z.json").is_file()
    assert sorted(p.name for p in (dry_root / "meta" / "patches").iterdir()) == ["node1.json"]
    assert patch.read_text(encoding="utf-8") == before


def test_fl14_cli_refuses_traversal_node(tmp_path):
    env = dict(os.environ)
    env.pop("LIVE_GCS", None)
    env.pop("IOT_ASP_GCS_BUCKET", None)
    env["IOT_ASP_AUTOROUTE_DRY_ROOT"] = str(tmp_path)
    env["IOT_ASP_AUTOROUTE_DRY_RUN"] = "1"
    env["PYTHONPATH"] = str(PKG_ROOT)
    proc = subprocess.run(
        [sys.executable, "-m", "iot_asp_autoroute.features_live", "--node", "../patches/x", "--seed-demo"],
        cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 2, proc.stderr
    out = json.loads(proc.stdout.strip().splitlines()[-1])
    assert out["ok"] is False and "node id" in out["error"]
    assert not (tmp_path / "meta").exists()


# ── FL-15 unparseable ts is dropped, never string-sorted ─────────────────────


def test_fl15_jsonl_line_without_ts_is_dropped_not_latest(dry_root):
    pre = "meta/telemetry/node1/"
    lines = [
        json.dumps({"deviceId": "node1", "ts": "2026-09-08T00:00:09Z", "absA": 0.09, "soundBurst": True}),
        json.dumps({"deviceId": "node1", "absA": 0.01}),  # no ts → dropped (stem 'day' is not a ts)
        json.dumps({"deviceId": "node1", "ts": "garbage", "absA": 0.02}),
    ]
    _write(dry_root, pre + "day.jsonl", "\n".join(lines) + "\n")
    errors: list = []
    pts = fl.parse_telemetry_objects([pre + "day.jsonl"], errors=errors)
    assert [(p["ts"], p["absA"]) for p in pts] == [("2026-09-08T00:00:09Z", 0.09)]
    assert [e["line"] for e in errors] == [1, 2] and {e["error"] for e in errors} == {"unparseable ts"}

    res = fl.run_live("node1", 50)
    assert res["object"] == "meta/features/node1/2026-09-08T00-00-09Z.json"
    assert res["sourceCount"] == 1 and res["shriekBias"] is True
    feats = list((dry_root / "meta" / "features" / "node1").iterdir())
    assert [f.name for f in feats] == ["2026-09-08T00-00-09Z.json"]


def test_fl15_json_object_without_ts_uses_name_stem(dry_root):
    pre = "meta/telemetry/node1/"
    _write(dry_root, pre + "2026-09-08T00-00-05Z.json", json.dumps({"deviceId": "node1", "absA": 0.05}))
    _write(dry_root, pre + "notats.json", json.dumps({"deviceId": "node1", "absA": 0.06}))
    errors: list = []
    pts = fl.parse_telemetry_objects(fl.list_telemetry_names("node1"), errors=errors)
    assert [p["ts"] for p in pts] == ["2026-09-08T00:00:05Z"]
    assert errors == [{"object": pre + "notats.json", "line": 0, "error": "unparseable ts"}]


def test_fl09_env_gate(dry_root, monkeypatch):
    fl._seed_demo("node1")
    monkeypatch.setenv("LIVE_GCS", "1")
    res = fl.run_live("node1", 50, write=False)
    assert res["live"] is False
    assert res["uri"] is None
    assert not (dry_root / "meta" / "features").exists()

    # Both set → live gate opens; reads are stubbed so no GCS client is needed.
    monkeypatch.setenv("IOT_ASP_GCS_BUCKET", "bucket-name-placeholder")
    pts = fl.demo_points("node1")
    seen: dict = {}

    def fake_latest(node, limit=200):
        seen["dry_run_during"] = gcs_io.DRY_RUN
        seen["bucket_during"] = gcs_io.BUCKET
        return pts[-limit:]

    monkeypatch.setattr(fl, "latest_points", fake_latest)
    res_live = fl.run_live("node1", 50, write=False)
    assert res_live["ok"] is True and res_live["live"] is True
    assert res_live["uri"] is None and res_live["written"] is False
    assert seen == {"dry_run_during": False, "bucket_during": "bucket-name-placeholder"}
    assert gcs_io.DRY_RUN is True and gcs_io.BUCKET == ""  # restored
    assert not (dry_root / "meta" / "features").exists()
    assert not (dry_root / "meta" / "patches").exists()

    # Explicit live=True without a bucket is downgraded to the dry-run mirror.
    monkeypatch.delenv("IOT_ASP_GCS_BUCKET")
    assert fl.run_live("node1", 50, write=False, live=True)["live"] is False
    assert fl.env_live_gate() is False


def test_fl10_no_telemetry(dry_root):
    res = fl.run_live("ghost", write=True)
    assert res["ok"] is False
    assert "no telemetry" in res["error"]
    assert res["sourceCount"] == 0 and res["uri"] is None
    assert not (dry_root / "meta" / "features").exists()


# ── FL-11 CLI ────────────────────────────────────────────────────────────────


def test_fl11_cli_seed_demo_offline(tmp_path):
    env = dict(os.environ)
    env.pop("LIVE_GCS", None)
    env.pop("IOT_ASP_GCS_BUCKET", None)
    env["IOT_ASP_AUTOROUTE_DRY_ROOT"] = str(tmp_path)
    env["IOT_ASP_AUTOROUTE_DRY_RUN"] = "1"
    env["PYTHONPATH"] = str(PKG_ROOT)
    proc = subprocess.run(
        [sys.executable, "-m", "iot_asp_autoroute.features_live", "--node", "node1", "--limit", "50", "--seed-demo"],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout.strip().splitlines()[-1])
    assert out["ok"] is True and out["live"] is False
    assert out["uri"].startswith("file://") and out["sourceCount"] == 12
    assert len(list((tmp_path / "meta" / "features" / "node1").glob("*.json"))) == 1
    assert not (tmp_path / "meta" / "patches").exists()

    # ghost node → exit 2, no write
    proc2 = subprocess.run(
        [sys.executable, "-m", "iot_asp_autoroute.features_live", "--node", "ghost"],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc2.returncode == 2
    assert json.loads(proc2.stdout.strip())["ok"] is False


# ── FL-12 notebook sync ──────────────────────────────────────────────────────


def _md_code_blocks(text: str) -> list[str]:
    return [m.group(1) for m in re.finditer(r"```python\n(.*?)```", text, flags=re.S)]


def test_fl12_notebook_ipynb_and_md_in_sync():
    nb = json.loads(NB_IPYNB.read_text(encoding="utf-8"))
    assert nb["nbformat"] == 4
    assert isinstance(nb.get("nbformat_minor"), int)
    assert isinstance(nb["metadata"], dict)
    code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
    for c in nb["cells"]:
        assert set(c) >= {"cell_type", "metadata", "source"}
        if c["cell_type"] == "code":
            assert "execution_count" in c and "outputs" in c
    code = "".join("".join(c["source"]) for c in code_cells)
    for name in ("GCP_SA_JSON", "IOT_ASP_GCS_BUCKET", "LIVE_GCS"):
        assert f'userdata.get("{name}")' in code, name
    assert "features_live.run_live(" in code
    assert "meta/patches" not in code
    assert "services/autoroute-adk" in code
    # no secret-looking values
    assert not re.search(r"BEGIN (RSA |OPENSSH )?PRIVATE KEY", code)
    assert not re.search(r"AIza[0-9A-Za-z_-]{20,}", code)

    md = NB_MD.read_text(encoding="utf-8")
    for name in ("GCP_SA_JSON", "IOT_ASP_GCS_BUCKET", "LIVE_GCS"):
        assert f'userdata.get("{name}")' in md
    assert "run_live(" in md
    blocks = _md_code_blocks(md)
    assert [b for b in blocks] == ["".join(c["source"]) for c in code_cells]
    md_cells = [c for c in nb["cells"] if c["cell_type"] == "markdown"]
    for c in md_cells:
        assert "".join(c["source"]).strip() in md


# ── FL-16 dry-run write target resolves under DRY_ROOT/meta/features ────────


def test_fl16_assert_features_path_resolves_under_dry_root(dry_root):
    fl.assert_features_path("meta/features/node1/2026-09-08T00-00-00Z.json")
    with pytest.raises(ValueError, match="only under meta/features"):
        fl.assert_features_path("meta/telemetry/node1/x.json")
    with pytest.raises(ValueError, match="meta/patches"):
        fl.assert_features_path("meta/patches/node1.json")
    # a name that only *looks* safe but resolves elsewhere (symlinked node dir) is refused
    outside = dry_root / "elsewhere"
    outside.mkdir()
    (dry_root / "meta" / "features").mkdir(parents=True)
    (dry_root / "meta" / "features" / "linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="resolves outside"):
        fl.assert_features_path("meta/features/linked/2026-09-08T00-00-00Z.json")


# ── FL-13 constants ──────────────────────────────────────────────────────────


def test_fl13_constants():
    expected_columns = tuple(
        dict.fromkeys(TELEMETRY_FEATURE_COLUMNS + fl.SENSOR_COLUMNS)
    )
    assert fl.ALL_COLUMNS == expected_columns
    assert fl.MIC_DIFF_ALPHA == 0.85
    assert len(fl.SENSOR_COLUMNS) == 18
    assert len(set(fl.ALL_COLUMNS)) == len(fl.ALL_COLUMNS)
    assert fl.BAND_LF_THR_DB == -60.0 and fl.BAND_US_THR_DB == -55.0
    assert fl.SHRIEK_MIC_DIFF_DB == 6.0
    assert fl.FEATURES_PREFIX == "meta/features/" and fl.FORBIDDEN_PREFIX == "meta/patches"
    for name in ("mic_diff", "band_burst", "project_sensor_features", "parse_telemetry_objects",
                 "latest_points", "build_feature_record", "features_object_name",
                 "assert_not_patch_path", "assert_features_path", "validate_node",
                 "run_live", "_seed_demo", "main"):
        assert callable(getattr(fl, name)), name
