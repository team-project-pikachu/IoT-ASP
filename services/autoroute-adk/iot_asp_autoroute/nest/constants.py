"""Single source of truth for Smart Device Management (SDM) identifiers and quotas.

Every identifier and every number in this module is copied from a Google
developer-documentation page that was fetched for the #85 build, not from model
recall — with exactly one labelled exception, ``DEVICE_QUOTAS[TYPE_DISPLAY]``, which
is a deliberate conservative choice and is marked as such at its definition. Sources
are named per block; the full digest with fetch dates lives in
``reference/knowledge/nest-device-access/`` and the spec is
``docs/specs/85-nest-google-home-integration.md``.

stdlib only — this module must stay importable everywhere (CI, dry-run, Colab).
"""

from __future__ import annotations

from typing import Final

# --------------------------------------------------------------------------- #
# API surface
# Source: https://developers.google.com/nest/device-access/api
#         https://developers.google.com/nest/device-access/authorize
# --------------------------------------------------------------------------- #

SDM_API_BASE: Final[str] = "https://smartdevicemanagement.googleapis.com/v1"
SDM_OAUTH_SCOPE: Final[str] = "https://www.googleapis.com/auth/sdm.service"
SDM_TOKEN_ENDPOINT: Final[str] = "https://oauth2.googleapis.com/token"
# The Partner Connections Manager consent surface. `{project_id}` is the Device
# Access **project id** (a UUID from console.nest.google.com/device-access), which
# is NOT the Google Cloud project id.
PCM_AUTH_URL_TEMPLATE: Final[str] = (
    "https://nestservices.google.com/partnerconnections/{project_id}/auth"
    "?redirect_uri={redirect_uri}"
    "&access_type=offline"
    "&prompt=consent"
    "&client_id={client_id}"
    "&response_type=code"
    "&scope=" + SDM_OAUTH_SCOPE
)
DEVICE_ACCESS_CONSOLE: Final[str] = "https://console.nest.google.com/device-access"

# Authorization is not complete — and events are not delivered — until the first
# devices.list call succeeds with the new token.
# Source: https://developers.google.com/nest/device-access/authorize
REQUIRES_FIRST_LIST_CALL: Final[bool] = True

# --------------------------------------------------------------------------- #
# Pub/Sub event transport
# Source: https://developers.google.com/nest/device-access/api/events
#         https://developers.google.com/nest/device-access/subscribe-to-events
# --------------------------------------------------------------------------- #

PUBSUB_API_BASE: Final[str] = "https://pubsub.googleapis.com/v1"
# Device Access projects created after January 2025 must self-host the topic in
# their own Google Cloud project; older projects were given a Google-hosted
# `projects/sdm-prod/topics/enterprise-<project-id>` topic.
PUBSUB_LEGACY_TOPIC_TEMPLATE: Final[str] = "projects/sdm-prod/topics/enterprise-{project_id}"
PUBSUB_SELF_HOSTED_TOPIC_TEMPLATE: Final[str] = "projects/{gcp_project}/topics/{topic_id}"
PUBSUB_SUBSCRIPTION_TEMPLATE: Final[str] = "projects/{gcp_project}/subscriptions/{subscription_id}"
PUBSUB_SUBSCRIBER_SCOPES: Final[tuple[str, ...]] = (
    "https://www.googleapis.com/auth/pubsub",
    "https://www.googleapis.com/auth/cloud-platform",
)
PUBSUB_SUBSCRIBER_ROLE: Final[str] = "roles/pubsub.subscriber"
PUBSUB_PUBLISHER_ROLE: Final[str] = "roles/pubsub.publisher"

# --------------------------------------------------------------------------- #
# Device types
# Source: https://developers.google.com/nest/device-access/api/camera (and the
# sibling doorbell / display / thermostat device pages).
# --------------------------------------------------------------------------- #

TYPE_CAMERA: Final[str] = "sdm.devices.types.CAMERA"
TYPE_DOORBELL: Final[str] = "sdm.devices.types.DOORBELL"
TYPE_DISPLAY: Final[str] = "sdm.devices.types.DISPLAY"
TYPE_THERMOSTAT: Final[str] = "sdm.devices.types.THERMOSTAT"

CAMERA_LIKE_TYPES: Final[frozenset[str]] = frozenset({TYPE_CAMERA, TYPE_DOORBELL, TYPE_DISPLAY})

# --------------------------------------------------------------------------- #
# Traits
# Source: https://developers.google.com/nest/device-access/traits
# --------------------------------------------------------------------------- #

TRAIT_CAMERA_CLIP_PREVIEW: Final[str] = "sdm.devices.traits.CameraClipPreview"
TRAIT_CAMERA_EVENT_IMAGE: Final[str] = "sdm.devices.traits.CameraEventImage"
TRAIT_CAMERA_IMAGE: Final[str] = "sdm.devices.traits.CameraImage"
TRAIT_CAMERA_LIVE_STREAM: Final[str] = "sdm.devices.traits.CameraLiveStream"
TRAIT_CAMERA_MOTION: Final[str] = "sdm.devices.traits.CameraMotion"
TRAIT_CAMERA_PERSON: Final[str] = "sdm.devices.traits.CameraPerson"
TRAIT_CAMERA_SOUND: Final[str] = "sdm.devices.traits.CameraSound"
TRAIT_DOORBELL_CHIME: Final[str] = "sdm.devices.traits.DoorbellChime"
TRAIT_CONNECTIVITY: Final[str] = "sdm.devices.traits.Connectivity"
TRAIT_INFO: Final[str] = "sdm.devices.traits.Info"
TRAIT_SETTINGS: Final[str] = "sdm.devices.traits.Settings"

CAMERA_TRAITS: Final[frozenset[str]] = frozenset(
    {
        TRAIT_CAMERA_CLIP_PREVIEW,
        TRAIT_CAMERA_EVENT_IMAGE,
        TRAIT_CAMERA_IMAGE,
        TRAIT_CAMERA_LIVE_STREAM,
        TRAIT_CAMERA_MOTION,
        TRAIT_CAMERA_PERSON,
        TRAIT_CAMERA_SOUND,
    }
)

# --------------------------------------------------------------------------- #
# Events
# Sources: .../traits/device/camera-sound, .../camera-motion, .../camera-person,
#          .../camera-clip-preview, .../doorbell-chime, .../api/events
# --------------------------------------------------------------------------- #

EVENT_CAMERA_MOTION: Final[str] = "sdm.devices.events.CameraMotion.Motion"
EVENT_CAMERA_PERSON: Final[str] = "sdm.devices.events.CameraPerson.Person"
EVENT_CAMERA_SOUND: Final[str] = "sdm.devices.events.CameraSound.Sound"
EVENT_DOORBELL_CHIME: Final[str] = "sdm.devices.events.DoorbellChime.Chime"
EVENT_CLIP_PREVIEW: Final[str] = "sdm.devices.events.CameraClipPreview.ClipPreview"

KNOWN_EVENTS: Final[frozenset[str]] = frozenset(
    {
        EVENT_CAMERA_MOTION,
        EVENT_CAMERA_PERSON,
        EVENT_CAMERA_SOUND,
        EVENT_DOORBELL_CHIME,
        EVENT_CLIP_PREVIEW,
    }
)

# Event thread lifecycle on a device-action event.
# Source: https://developers.google.com/nest/device-access/api/events
EVENT_THREAD_STATES: Final[frozenset[str]] = frozenset({"STARTED", "UPDATED", "ENDED"})

# Relation event types (structure ↔ device membership changes).
RELATION_TYPES: Final[frozenset[str]] = frozenset({"CREATED", "UPDATED", "DELETED"})

# "Event images expire 30 seconds after the event is published."
# Source: https://developers.google.com/nest/device-access/api/events
EVENT_IMAGE_TTL_S: Final[float] = 30.0

# --------------------------------------------------------------------------- #
# Commands
# Source: https://developers.google.com/nest/device-access/api/camera
# --------------------------------------------------------------------------- #

CMD_GENERATE_IMAGE: Final[str] = "sdm.devices.commands.CameraEventImage.GenerateImage"
CMD_GENERATE_RTSP: Final[str] = "sdm.devices.commands.CameraLiveStream.GenerateRtspStream"
CMD_EXTEND_RTSP: Final[str] = "sdm.devices.commands.CameraLiveStream.ExtendRtspStream"
CMD_STOP_RTSP: Final[str] = "sdm.devices.commands.CameraLiveStream.StopRtspStream"
CMD_GENERATE_WEBRTC: Final[str] = "sdm.devices.commands.CameraLiveStream.GenerateWebRtcStream"
CMD_EXTEND_WEBRTC: Final[str] = "sdm.devices.commands.CameraLiveStream.ExtendWebRtcStream"
CMD_STOP_WEBRTC: Final[str] = "sdm.devices.commands.CameraLiveStream.StopWebRtcStream"

# --------------------------------------------------------------------------- #
# Documented quotas — the whole reason this integration paces instead of bursting
# Source: https://developers.google.com/nest/device-access/project/limits
#
# Each entry is (queries_per_minute, queries_per_hour | None). `None` means the
# page documents no hourly cap for that unit. Numbers are verbatim from the
# "Sandbox rate limits" tables; a launched project must re-verify before raising
# any of them (see docs/specs/85-nest-google-home-integration.md "Risks").
# --------------------------------------------------------------------------- #

METHOD_DEVICES_LIST: Final[str] = "devices.list"
METHOD_DEVICES_GET: Final[str] = "devices.get"
METHOD_DEVICES_EXECUTE_COMMAND: Final[str] = "devices.executeCommand"
METHOD_STRUCTURES_LIST: Final[str] = "structures.list"
METHOD_STRUCTURES_GET: Final[str] = "structures.get"
METHOD_ROOMS_LIST: Final[str] = "structures.rooms.list"
METHOD_ROOMS_GET: Final[str] = "structures.rooms.get"

METHOD_QUOTAS: Final[dict[str, tuple[int, int | None]]] = {
    METHOD_DEVICES_LIST: (5, None),
    METHOD_DEVICES_GET: (10, None),
    METHOD_DEVICES_EXECUTE_COMMAND: (10, None),
    METHOD_STRUCTURES_LIST: (5, None),
    METHOD_STRUCTURES_GET: (5, None),
    METHOD_ROOMS_LIST: (5, None),
    METHOD_ROOMS_GET: (5, None),
}

# Per device instance, per project, per user.
#
# The limits page tabulates exactly three device types — THERMOSTAT, CAMERA, DOORBELL —
# and states: "If a device type is not listed below, it does not have device instance
# level rate limits."
#
# DISPLAY is therefore NOT a documented row. The value below is an UNVERIFIED,
# deliberately conservative extrapolation from CAMERA: a Nest Hub Max exposes the camera
# traits, and pacing a device more strictly than the vendor requires can only cost
# freshness, never a RESOURCE_EXHAUSTED. Do not cite it as documented, and re-check the
# page before relaxing it.
DEVICE_QUOTAS: Final[dict[str, tuple[int, int | None]]] = {
    TYPE_CAMERA: (30, 100),
    TYPE_DOORBELL: (30, 100),
    TYPE_DISPLAY: (30, 100),  # UNVERIFIED — see note above
    TYPE_THERMOSTAT: (5, 100),
}

#: Device types whose instance quota is quoted verbatim from the limits page.
DOCUMENTED_DEVICE_QUOTAS: Final[frozenset[str]] = frozenset(
    {TYPE_CAMERA, TYPE_DOORBELL, TYPE_THERMOSTAT}
)

# "Each trait command is limited to 5 QPM per project, per user, per device."
TRAIT_COMMAND_QPM: Final[int] = 5

# Sandbox account caps (not rate limits — account structure limits).
SANDBOX_MAX_PROJECTS: Final[int] = 3
SANDBOX_MAX_USERS: Final[int] = 25
SANDBOX_MAX_STRUCTURES: Final[int] = 5
SANDBOX_MAX_USERS_PER_STRUCTURE: Final[int] = 5

# Error surfaced when a quota is exceeded.
# Source: https://developers.google.com/nest/device-access/project/limits
RATE_LIMIT_RPC_CODE: Final[str] = "RESOURCE_EXHAUSTED"
RATE_LIMIT_HTTP_STATUS: Final[int] = 429


def min_interval_s(qpm: int, qph: int | None = None) -> float:
    """Minimum sustainable seconds between calls under both windows.

    The binding constraint is whichever window allows *fewer* calls per second.
    A camera at ``(30 QPM, 100 QPH)`` may briefly run at 2.0 s spacing but can
    only sustain ``3600 / 100 = 36.0`` s, so 36.0 is what a continuous poller
    must use as its steady-state cadence.

    >>> min_interval_s(5)
    12.0
    >>> min_interval_s(30, 100)
    36.0
    """
    if qpm <= 0:
        raise ValueError(f"qpm must be positive, got {qpm}")
    per_minute = 60.0 / float(qpm)
    if qph is None:
        return per_minute
    if qph <= 0:
        raise ValueError(f"qph must be positive when given, got {qph}")
    return max(per_minute, 3600.0 / float(qph))


def method_min_interval_s(method: str) -> float:
    """Steady-state seconds between calls of one SDM method (project-wide)."""
    try:
        qpm, qph = METHOD_QUOTAS[method]
    except KeyError:  # pragma: no cover - guarded by tests
        raise ValueError(f"unknown SDM method: {method}") from None
    return min_interval_s(qpm, qph)


def device_min_interval_s(device_type: str) -> float:
    """Steady-state seconds between calls against one device instance."""
    qpm, qph = DEVICE_QUOTAS.get(device_type, DEVICE_QUOTAS[TYPE_CAMERA])
    return min_interval_s(qpm, qph)


def max_cameras_at_cadence(cadence_s: float) -> int:
    """How many cameras a project-wide ``devices.get`` budget supports.

    ``devices.get`` is 10 QPM project-wide, so polling N cameras every
    ``cadence_s`` seconds needs ``N / cadence_s`` calls per second and must stay
    under ``10 / 60``. At the per-camera floor of 36 s that is 6 cameras.

    >>> max_cameras_at_cadence(36.0)
    6
    """
    if cadence_s <= 0:
        raise ValueError(f"cadence_s must be positive, got {cadence_s}")
    qpm, qph = METHOD_QUOTAS[METHOD_DEVICES_GET]
    budget_per_s = min(qpm / 60.0, (qph / 3600.0) if qph else float("inf"))
    return int(budget_per_s * cadence_s)


# Default continuous cadences, derived (never hand-tuned below the floors above).
DEFAULT_LIST_CADENCE_S: Final[float] = method_min_interval_s(METHOD_DEVICES_LIST)  # 12.0
DEFAULT_CAMERA_CADENCE_S: Final[float] = device_min_interval_s(TYPE_CAMERA)  # 36.0

# Backoff on RESOURCE_EXHAUSTED / 5xx: exponential with full jitter, capped.
BACKOFF_BASE_S: Final[float] = 2.0
BACKOFF_MAX_S: Final[float] = 300.0

# --------------------------------------------------------------------------- #
# Secret names — values never live in git, chat, logs or issues (CLAUDE.md #10).
# Resolution order: process env → Secret Manager (bear-iot-asp-rec) → 1Password
# Environment `dev`. See docs/nest-device-access.md.
# --------------------------------------------------------------------------- #

ENV_DA_PROJECT_ID: Final[str] = "NEST_DA_PROJECT_ID"
ENV_OAUTH_CLIENT_ID: Final[str] = "NEST_OAUTH_CLIENT_ID"
ENV_OAUTH_CLIENT_SECRET: Final[str] = "NEST_OAUTH_CLIENT_SECRET"
ENV_REFRESH_TOKEN: Final[str] = "NEST_REFRESH_TOKEN"
ENV_PUBSUB_SUBSCRIPTION: Final[str] = "NEST_PUBSUB_SUBSCRIPTION"
ENV_GCP_PROJECT: Final[str] = "GOOGLE_CLOUD_PROJECT"

SECRET_NAMES: Final[tuple[str, ...]] = (
    ENV_DA_PROJECT_ID,
    ENV_OAUTH_CLIENT_ID,
    ENV_OAUTH_CLIENT_SECRET,
    ENV_REFRESH_TOKEN,
)

# --------------------------------------------------------------------------- #
# ASP wire mapping (additive on schemaVersion 1 — docs/api-contract.md)
# --------------------------------------------------------------------------- #

#: SDM event identifier → ASP ``nestEvent`` wire value.
EVENT_WIRE_NAMES: Final[dict[str, str]] = {
    EVENT_CAMERA_MOTION: "motion",
    EVENT_CAMERA_PERSON: "person",
    EVENT_CAMERA_SOUND: "sound",
    EVENT_DOORBELL_CHIME: "chime",
    EVENT_CLIP_PREVIEW: "clip_preview",
}

#: ASP ``nestEvent`` values that count as an acoustic observation (#86 #96 #103).
ACOUSTIC_EVENTS: Final[frozenset[str]] = frozenset({"sound", "chime"})

GCS_NEST_EVENT_PREFIX: Final[str] = "meta/nest/events"
GCS_NEST_STATE_PREFIX: Final[str] = "meta/nest/state"
