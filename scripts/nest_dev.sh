#!/usr/bin/env bash
# Offline dry-run for the IoT-ASP × Nest Device Access poller (#85).
#
# No credentials, no network, no GCP: a fake transport answers devices.list /
# devices.get from Google's own documentation placeholders (project-id, device-id),
# and the SDM event fixtures under tests/fixtures/nest/ are replayed through a fake
# Pub/Sub puller. Everything the poller ingests lands in the .autoroute-dry/ mirror,
# exactly as scripts/autoroute_dev.sh does for the autoroute path.
#
# Prints "OK nest_dev" on success; exits non-zero on any failure.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export IOT_ASP_AUTOROUTE_DRY_RUN=1
export IOT_ASP_AUTOROUTE_DRY_ROOT="${IOT_ASP_AUTOROUTE_DRY_ROOT:-${ROOT}/.autoroute-dry}"
export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-bear-iot-asp-rec}"
export PYTHONPATH="${ROOT}/services/autoroute-adk${PYTHONPATH:+:$PYTHONPATH}"
# Secret NAMES only; the dry-run never reads a value and never signs a request.
unset NEST_OAUTH_CLIENT_SECRET NEST_REFRESH_TOKEN 2>/dev/null || true
cd "$ROOT"

python3 - <<'PY'
"""Fixtures -> mapper -> fake-transport SdmClient -> NestPoller -> .autoroute-dry/."""

from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

from iot_asp_autoroute.nest import constants, events, mapping, poller
from iot_asp_autoroute.nest.rate_limit import SdmRateLimiter
from iot_asp_autoroute.nest.sdm_client import SdmClient

ROOT = Path(os.environ["PYTHONPATH"].split(os.pathsep)[0]).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "nest"
DRY_ROOT = Path(os.environ["IOT_ASP_AUTOROUTE_DRY_ROOT"]).resolve()
NODE = "node1"

# Google's documentation placeholders — never a real SDM id (CLAUDE.md #7).
# https://developers.google.com/nest/device-access/api/camera
DEVICES = [
    {
        "name": "enterprises/project-id/devices/device-id",
        "type": constants.TYPE_CAMERA,
        "traits": {
            constants.TRAIT_CAMERA_SOUND: {},
            constants.TRAIT_CAMERA_MOTION: {},
            constants.TRAIT_CONNECTIVITY: {"status": "ONLINE"},
        },
    },
    {
        "name": "enterprises/project-id/devices/device-id-2",
        "type": constants.TYPE_DOORBELL,
        "traits": {
            constants.TRAIT_DOORBELL_CHIME: {},
            constants.TRAIT_CONNECTIVITY: {"status": "ONLINE"},
        },
    },
]


class FakeClock:
    """Simulated monotonic clock; only ``sleep`` moves it. No wall-clock waiting."""

    def __init__(self, start: float = 0.0) -> None:
        self.t = float(start)

    def __call__(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        assert seconds >= 0.0, f"negative sleep {seconds}"
        self.t += float(seconds)


class FakeAuth:
    """Never touches the token endpoint; the value is a literal placeholder."""

    def access_token(self) -> str:
        return "fake-access-token"

    def status(self) -> dict:
        return {"hasRefreshToken": False, "expiresInS": None}


def fake_transport(method, url, headers, body=None):
    """Answer devices.list / devices.get offline. Any other URL is a failure."""
    if url.endswith("/devices"):
        return 200, {}, json.dumps({"devices": DEVICES}).encode("utf-8")
    for dev in DEVICES:
        if url.endswith("/" + dev["name"].rsplit("/", 1)[-1]):
            return 200, {}, json.dumps(dev).encode("utf-8")
    raise AssertionError(f"nest_dev must not reach the network: {method} {url}")


class FixturePuller:
    """Replays tests/fixtures/nest/*.json as if Pub/Sub had delivered them."""

    def __init__(self, paths):
        self.queue = []
        for i, path in enumerate(paths):
            envelope = json.loads(path.read_text(encoding="utf-8"))
            self.queue.append((f"ack-{i}", events.parse_event(envelope), path.name))
        self.acked = []
        self.pulls = 0

    def pull(self, *, max_messages: int = 10):
        self.pulls += 1
        batch, self.queue = self.queue[:max_messages], self.queue[max_messages:]
        return [(ack, ev) for ack, ev, _name in batch]

    def acknowledge(self, ack_ids) -> None:
        self.acked.extend(ack_ids)

    def status(self) -> dict:
        return {"pulls": self.pulls, "acks": len(self.acked), "queued": len(self.queue)}


def _patch_tree_fingerprint() -> dict:
    """Existence + mtime + size of every object under the dry-run meta/patches tree.

    The mirror is shared with scripts/autoroute_dev.sh, which legitimately writes
    patches; the invariant this run proves is that *nest_dev touched none of them*.
    """
    root = DRY_ROOT / "meta" / "patches"
    if not root.exists():
        return {}
    return {
        str(p.relative_to(DRY_ROOT)): (p.stat().st_mtime_ns, p.stat().st_size)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def main() -> int:
    patches_before = _patch_tree_fingerprint()
    fixtures = sorted(p for p in FIXTURES.glob("*.json") if p.name != "pubsub_pull_response.json")
    if not fixtures:
        print(f"FAIL nest_dev: no fixtures under {FIXTURES}", file=sys.stderr)
        return 2
    print(f"fixtures: {[p.name for p in fixtures]}")

    # 1. mapper only — every fixture must map to telemetry with no patch/control key.
    mapped = 0
    for path in fixtures:
        ev = events.parse_event(json.loads(path.read_text(encoding="utf-8")))
        if ev is None:
            print(f"  {path.name}: not an SDM envelope (ignored)")
            continue
        tel = mapping.event_to_telemetry(ev, node_id=NODE, now=1767225600.0)
        poller.assert_telemetry_only(tel)
        assert tel["schemaVersion"] == 1, tel
        assert "previewUrl" not in json.dumps(tel), "recording URI reached the wire"
        mapped += 1
        print(f"  {path.name}: nestEvent={tel.get('nestEvent')} soundBurst={tel.get('soundBurst')}")
    print(f"mapped: {mapped}/{len(fixtures)}")

    # 2. full poller over a simulated clock, fake transport, fixture events.
    clock = FakeClock(0.0)
    limiter = SdmRateLimiter(rng=random.Random(85))
    client = SdmClient(
        FakeAuth(),
        da_project_id="project-id",
        limiter=limiter,
        transport=fake_transport,
        clock=clock,
    )
    puller = FixturePuller(fixtures)
    np = poller.NestPoller(
        client,
        node_id=NODE,
        puller=puller,
        limiter=limiter,
        clock=clock,
        wall_clock=lambda: 1767225600.0 + clock.t,
        rng=random.Random(85),
        hold_manual=True,  # negative control: observation continues, authorship does not
    )
    summary = np.run_forever(sleep=clock.sleep, max_steps=40)
    print("run:", json.dumps(summary, sort_keys=True))

    health = np.health()
    health_dedupe = health.get("deduper")
    print(
        "health:",
        json.dumps(
            {k: health[k] for k in
             ("devices", "listCadenceS", "effectiveCameraCadenceS", "eventsCadenceS",
              "consecutiveErrors", "holdManual", "writesPatches")},
            sort_keys=True,
        ),
    )

    # 3. assertions — the things this dry-run exists to prove.
    ok = True

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal ok
        print(f"  [{'PASS' if cond else 'FAIL'}] {label}{(' — ' + detail) if detail else ''}")
        ok = ok and bool(cond)

    check("no errors", summary["errors"] == 0, str(summary.get("errors")))
    check("SDM calls made", summary["calls"] > 0, f"calls={summary['calls']}")
    # Fewer than `mapped` is expected: EventDeduper collapses a STARTED/UPDATED/ENDED
    # thread and repeated eventSessionIds down to one handled event.
    check(
        "events ingested",
        summary["events"] > 0,
        f"events={summary['events']} deduper={health_dedupe}",
    )
    check("telemetry written", summary["telemetry"] > 0, f"rows={summary['telemetry']}")
    check("devices discovered", health["devices"] == len(DEVICES))
    check("hold/manual observed", health["holdManual"] is True)

    tel_root = DRY_ROOT / "meta" / "telemetry" / NODE
    rows = sorted(tel_root.glob("*.json")) if tel_root.exists() else []
    check("telemetry objects on disk", bool(rows), f"{len(rows)} under {tel_root}")

    # Hold / Manual + invariant #2: the poller writes no patch and edits none.
    patches_after = _patch_tree_fingerprint()
    check(
        "meta/patches untouched",
        patches_after == patches_before,
        f"{len(patches_before)} pre-existing object(s) from scripts/autoroute_dev.sh, "
        f"{len(patches_after)} after",
    )

    # The guards themselves refuse, rather than the run merely not tripping them.
    for bad in ("meta/patches/node1.json", "meta/patches/../telemetry/x.json"):
        try:
            poller.assert_not_patch_path(bad)
        except poller.PatchWriteRefused:
            check(f"guard refuses {bad!r}", True)
        else:
            check(f"guard refuses {bad!r}", False)
    try:
        poller.assert_telemetry_only({"deviceId": NODE, "vol": 100, "holdManual": False})
    except poller.PatchWriteRefused:
        check("guard refuses a patch field on the wire", True)
    else:
        check("guard refuses a patch field on the wire", False)

    # A cadence faster than the documented floor must be refused, not clamped.
    try:
        poller.NestPoller(client, node_id=NODE, camera_cadence_s=1.0)
    except ValueError:
        check("cadence faster than the floor refused", True)
    else:
        check("cadence faster than the floor refused", False)

    if not ok:
        print("FAIL nest_dev", file=sys.stderr)
        return 2
    print("OK nest_dev")
    return 0


raise SystemExit(main())
PY
