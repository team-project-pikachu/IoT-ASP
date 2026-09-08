"""GCS helpers for telemetry ingest + patch write (dry-run uses local mirror)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "bear-iot-asp-rec")
BUCKET = os.environ.get("IOT_ASP_GCS_BUCKET", "")
DRY_RUN = os.environ.get("IOT_ASP_AUTOROUTE_DRY_RUN", "1") not in ("0", "false", "False")


def _default_dry_root() -> Path:
    """Resolve dry-run mirror root for both repo checkout and Cloud Run image.

    Repo layout: ``<repo>/services/autoroute-adk/iot_asp_autoroute/gcs_io.py``
    → ``parents[3]`` is the repo root (``.autoroute-dry``).

    Container layout (``Dockerfile`` copies package to ``/app/iot_asp_autoroute``)
    → only ``parents[0..1]`` exist; fall back to ``/tmp`` so import never raises
    ``IndexError`` (live GCS path does not use the dry root when bucket + live).
    """
    here = Path(__file__).resolve()
    try:
        return here.parents[3] / ".autoroute-dry"
    except IndexError:
        return Path(os.environ.get("TMPDIR", "/tmp")) / "iot-asp-autoroute-dry"


DRY_ROOT = Path(os.environ.get("IOT_ASP_AUTOROUTE_DRY_ROOT", str(_default_dry_root())))


def is_dry_run() -> bool:
    return DRY_RUN or not BUCKET


def _local_path(object_name: str) -> Path:
    p = DRY_ROOT / object_name
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def write_json(object_name: str, payload: dict[str, Any]) -> str:
    body = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if is_dry_run():
        path = _local_path(object_name)
        path.write_text(body, encoding="utf-8")
        return f"file://{path}"
    from google.cloud import storage  # type: ignore

    client = storage.Client(project=PROJECT)
    blob = client.bucket(BUCKET).blob(object_name)
    blob.upload_from_string(body, content_type="application/json")
    return f"gs://{BUCKET}/{object_name}"


def read_json(object_name: str) -> dict[str, Any] | None:
    if is_dry_run():
        path = _local_path(object_name)
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    from google.cloud import storage  # type: ignore

    client = storage.Client(project=PROJECT)
    blob = client.bucket(BUCKET).blob(object_name)
    if not blob.exists():
        return None
    return json.loads(blob.download_as_text())


def list_prefix(prefix: str) -> list[str]:
    if is_dry_run():
        root = DRY_ROOT / prefix
        if not root.exists():
            return []
        return sorted(
            str(p.relative_to(DRY_ROOT))
            for p in root.rglob("*.json")
            if p.is_file()
        )
    from google.cloud import storage  # type: ignore

    client = storage.Client(project=PROJECT)
    return [b.name for b in client.list_blobs(BUCKET, prefix=prefix)]
