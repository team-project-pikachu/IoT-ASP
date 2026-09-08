"""Non-PII experiment cipher tags (Blake2b), not cryptographic wire secrets."""

from __future__ import annotations

import hashlib
import re
from typing import Any

_SAFE = re.compile(r"^[a-zA-Z0-9._:-]{1,64}$")


def experiment_tag(
    label: str,
    *,
    salt: str = "iot-asp-timestore-v0",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a compact non-PII tag for diversity / cipher hooks.

    ``label`` must be alphanumeric / ``._:-`` only (no streets, phones, emails).
    """
    if not _SAFE.match(label):
        raise ValueError(
            "experiment label must be non-PII token matching "
            r"^[a-zA-Z0-9._:-]{1,64}$"
        )
    payload = f"{salt}|{label}".encode("utf-8")
    digest = hashlib.blake2b(payload, digest_size=8).hexdigest()
    out: dict[str, Any] = {
        "cipher": "blake2b-64",
        "label": label,
        "tag": digest,
        "pii": False,
    }
    if meta:
        # Only allow already-safe scalar meta keys (caller responsibility).
        out["meta"] = {str(k): meta[k] for k in list(meta)[:8]}
    return out
