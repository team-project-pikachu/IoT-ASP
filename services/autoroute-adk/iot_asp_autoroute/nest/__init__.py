"""Google Nest Device Access (SDM API) integration for the IoT-ASP fleet.

Continuous, quota-paced observation of Nest cameras/doorbells (#84 #85 #86 #94 #103)
feeding the existing schemaVersion-1 telemetry wire. Import-safe with stdlib only:
every optional dependency (google-cloud-pubsub, google-auth) is imported lazily
inside the function that needs it, so `import iot_asp_autoroute.nest` never fails
in CI or the offline dry-run.

Public surface is re-exported here; submodules stay importable on their own.
"""

from __future__ import annotations

from . import constants  # noqa: F401  (stdlib-only, always safe)

__all__ = ["constants"]

for _name in ("rate_limit", "auth", "sdm_client", "events", "mapping", "poller"):
    try:  # pragma: no cover - exercised by tests/test_nest_import.py
        globals()[_name] = __import__(f"{__name__}.{_name}", fromlist=[_name])
        __all__.append(_name)
    except Exception:  # noqa: BLE001 - soft-fail like the ADK agent import
        pass
