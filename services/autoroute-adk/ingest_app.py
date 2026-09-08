"""Cloud Run HTTP surface for phone telemetry + patch poll (#61).

Deploy from this directory (see ``scripts/deploy_ingest_cloudrun.sh``).
Runtime env (Secret Manager / Cloud Run — never commit values that are secrets):

- ``GOOGLE_CLOUD_PROJECT`` (default ``bear-iot-asp-rec``)
- ``IOT_ASP_GCS_BUCKET`` — private fleet bucket name
- ``IOT_ASP_AUTOROUTE_DRY_RUN=0`` for live GCS writes
- ``IOT_ASP_AUTOROUTE_ON_INGEST=0`` — keep ingest write-only unless ADK author is ready (#60)

Phones: ``?telemetry=<service>/ingest&patch=<service>/patch.json`` or bake
``BACKEND_BASE_URL`` in ``public/index.html``.
"""

from __future__ import annotations

import json
import os
from typing import Any

from flask import Flask, Request, Response, request

os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "bear-iot-asp-rec")

app = Flask(__name__)

# Offline / cold-start fallback when GCS has no authored patch yet (matches public/patch.json).
_DEFAULT_PATCH: dict[str, Any] = {
    "schemaVersion": 1,
    "algo": "am_gate",
    "fMin": 17000,
    "fMax": 21000,
    "vol": 100,
    "pulseMs": 100,
    "shriekMs": 60,
    "vibThreshold": 0.12,
    "seedAction": "keep",
    "rationale": "Ingest service fallback mock when meta/patches/<node>.json is absent.",
    "engineId": "iot-asp-autoroute",
    "trigger": "ingest-fallback-mock",
}


def _cors(resp: Response) -> Response:
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Max-Age"] = "86400"
    return resp


def _json(payload: dict[str, Any], status: int = 200) -> Response:
    return _cors(
        Response(
            json.dumps(payload, separators=(",", ":")),
            status=status,
            mimetype="application/json",
        )
    )


def _parse_body(req: Request) -> tuple[dict[str, Any] | None, Response | None]:
    body = req.get_json(silent=True)
    if body is None and req.data:
        try:
            body = json.loads(req.data.decode("utf-8"))
        except Exception:
            return None, _json({"ok": False, "error": "invalid JSON"}, 400)
    if body is None:
        body = {}
    if not isinstance(body, dict):
        return None, _json({"ok": False, "error": "JSON object required"}, 400)
    return body, None


@app.get("/healthz")
def healthz() -> Response:
    return _json(
        {
            "ok": True,
            "service": "iot-asp-ingest",
            "dryRun": os.environ.get("IOT_ASP_AUTOROUTE_DRY_RUN", "1"),
            "bucketSet": bool(os.environ.get("IOT_ASP_GCS_BUCKET")),
        }
    )


@app.route("/ingest", methods=["POST", "OPTIONS"])
@app.route("/", methods=["POST", "OPTIONS"])
def ingest_route() -> Response:
    if request.method == "OPTIONS":
        return _cors(Response("", status=204))

    body, err = _parse_body(request)
    if err is not None:
        return err
    assert body is not None

    from iot_asp_autoroute.tools import ingest_telemetry, process_sudden_freq

    result = ingest_telemetry(json.dumps(body))
    node = str(body.get("deviceId") or body.get("nodeId") or "node1")
    if result.get("suddenFreq") and os.environ.get("IOT_ASP_AUTOROUTE_ON_INGEST", "0") not in (
        "0",
        "false",
        "False",
    ):
        result["patch"] = process_sudden_freq(node)
    return _json(result, 200 if result.get("ok") else 400)


@app.get("/patch.json")
def patch_json() -> Response:
    """Hot-apply poll target: GCS ``meta/patches/<node>.json`` or fallback mock."""
    node = str(request.args.get("node") or request.args.get("deviceId") or "node1")
    # Keep node path-safe (same spirit as tools.validate_node without importing heavy clamps path).
    if not node.replace("-", "").replace("_", "").isalnum() or len(node) > 64:
        return _json({"ok": False, "error": "invalid node"}, 400)

    from iot_asp_autoroute import gcs_io

    data = gcs_io.read_json(f"meta/patches/{node}.json") or dict(_DEFAULT_PATCH)
    resp = _cors(
        Response(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            status=200,
            mimetype="application/json",
        )
    )
    resp.headers["Cache-Control"] = "no-store"
    return resp


if __name__ == "__main__":  # pragma: no cover
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
