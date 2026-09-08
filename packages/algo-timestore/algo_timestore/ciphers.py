"""Non-PII experiment cipher tags (Blake2b), not cryptographic wire secrets."""

from __future__ import annotations

import hashlib
from typing import Final

# Experiment IDs are opaque constants registered in source so user-provided labels,
# phone numbers, email addresses, and locations can never enter cipher payloads.
FAIRFAX_CIRCLE_SIM_ID: Final = "exp_8a9f0d2c6b7e4a11"
REGISTERED_EXPERIMENT_IDS: Final = frozenset({FAIRFAX_CIRCLE_SIM_ID})


def experiment_tag(
    experiment_id: str,
    *,
    salt: str = "iot-asp-timestore-v0",
) -> dict[str, str | bool]:
    """Return a compact tag for a source-registered opaque experiment ID."""
    if experiment_id not in REGISTERED_EXPERIMENT_IDS:
        raise ValueError("experiment_id must be a registered opaque experiment ID")
    payload = f"{salt}|{experiment_id}".encode("utf-8")
    digest = hashlib.blake2b(payload, digest_size=8).hexdigest()
    return {
        "cipher": "blake2b-64",
        "experimentId": experiment_id,
        "tag": digest,
        "pii": False,
    }
