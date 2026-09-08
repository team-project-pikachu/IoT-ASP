"""Quota-paced REST client for the Smart Device Management (SDM) API.

Issue #85 / #84 / #94, spec ``docs/specs/85-nest-google-home-integration.md``.

The whole point of this module is that it **never bursts**. Every SDM call asks
the injected limiter first; if the budget is not yet available the call raises
:class:`SdmThrottled` carrying ``retry_at``. The client does not sleep, does not
retry in a loop, and does not queue — the poller owns time (NEST_DESIGN.md #8).

Verified API facts (each carries the page that states it):

* ``devices.list`` — ``GET {base}/enterprises/{project-id}/devices``
* ``devices.get``  — ``GET {base}/enterprises/{project-id}/devices/{device-id}``
* ``devices.executeCommand`` —
  ``POST {base}/enterprises/{project-id}/devices/{device-id}:executeCommand``
  with body ``{"command": ..., "params": {...}}``
* A device object carries ``name``, ``type``, ``traits``, ``parentRelations``
  (each with ``parent`` and ``displayName``) and ``assignee``.
  All four: https://developers.google.com/nest/device-access/api
* Requests are authorized with ``Authorization: Bearer <access token>`` — same
  page.
* ``sdm.devices.traits.Connectivity`` has a single field ``status`` whose value
  is ``"ONLINE"`` or ``"OFFLINE"`` —
  https://developers.google.com/nest/device-access/traits/device/connectivity
* Error taxonomy (RPC code ⇄ HTTP status) is transcribed verbatim from
  https://developers.google.com/nest/device-access/reference/errors/api into
  :data:`HTTP_TO_RPC` / :data:`RETRYABLE_RPC_CODES`. ``Rate limited.`` is
  ``429 / RESOURCE_EXHAUSTED``; ``Permission denied.`` is ``403 /
  PERMISSION_DENIED``; ``Camera image is no longer available for download.`` is
  ``504 / DEADLINE_EXCEEDED``. No code in that table was invented here.
* The error body is the standard Google shape
  ``{"error": {"code": int, "message": str, "status": "<RPC CODE>"}}`` —
  https://google.aip.dev/193 (AIP-193).

**The download-auth trap.** Two different Authorization schemes, both verified:

* An **event image** from ``CameraEventImage.GenerateImage`` returns
  ``{"results": {"url": ..., "token": ...}}`` and is downloaded with
  ``Authorization: Basic <token>`` — literally ``curl -H "Authorization: Basic
  g.0.eventToken" https://domain/sdm_event_snapshot/...``. It also accepts a
  ``width`` or ``height`` query parameter (default width 480) and the image
  expires 30 s after the event is published
  (:data:`constants.EVENT_IMAGE_TTL_S`) —
  https://developers.google.com/nest/device-access/api/camera
* A **CameraClipPreview** ``previewUrl`` is downloaded with the ordinary OAuth
  access token: ``curl -H 'Authorization: Bearer access-token' https://...`` —
  https://developers.google.com/nest/device-access/traits/device/camera-clip-preview

:meth:`SdmClient.download` therefore takes ``bearer=`` **or** ``basic=`` and
refuses to guess.

House rules: stdlib only, no ``google-*`` import, injectable transport so tests
are offline, no sleeps, and no credential value in any ``repr`` or exception
message. ``previewUrl`` and raw device ids are site identifiers (CLAUDE.md #7):
this module handles them in memory but never puts them on the public wire — that
is ``mapping.device_ref``'s job.
"""

from __future__ import annotations

import json
import time
import urllib.parse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Callable

from . import constants
from .auth import Transport, urllib_transport

__all__ = [
    "SdmError",
    "SdmAuthError",
    "SdmRateLimited",
    "SdmThrottled",
    "NestDevice",
    "SdmClient",
    "HTTP_TO_RPC",
    "RETRYABLE_RPC_CODES",
]

# ── error taxonomy ───────────────────────────────────────────────────────────
# Transcribed from the SDM API error reference. Only codes that actually appear
# in that table (plus the AIP-193 standard names for transport-level failures)
# are listed; nothing here is guessed.
# https://developers.google.com/nest/device-access/reference/errors/api

#: HTTP status → RPC code, for responses whose body has no ``error.status``.
HTTP_TO_RPC: dict[int, str] = {
    400: "INVALID_ARGUMENT",  # "Command not supported." / "Contains an invalid value."
    401: "UNAUTHENTICATED",  # UNVERIFIED: not in the SDM error table; AIP-193 default.
    403: "PERMISSION_DENIED",  # "Permission denied."
    404: "NOT_FOUND",  # "Device not found." / "Enterprise not found."
    429: constants.RATE_LIMIT_RPC_CODE,  # "Rate limited." → RESOURCE_EXHAUSTED
    500: "INTERNAL",  # UNVERIFIED: not in the SDM error table.
    503: "UNAVAILABLE",  # UNVERIFIED: not in the SDM error table.
    504: "DEADLINE_EXCEEDED",  # "Camera image is no longer available for download."
}

#: RPC codes worth trying again later. ``FAILED_PRECONDITION``,
#: ``INVALID_ARGUMENT``, ``NOT_FOUND`` and ``PERMISSION_DENIED`` are NOT here —
#: the SDM error table shows them as caller mistakes, so retrying only burns
#: quota.
RETRYABLE_RPC_CODES: frozenset[str] = frozenset(
    {constants.RATE_LIMIT_RPC_CODE, "DEADLINE_EXCEEDED", "UNAVAILABLE", "INTERNAL"}
)

#: RPC codes that mean "the token is wrong", not "the request is wrong".
_AUTH_RPC_CODES: frozenset[str] = frozenset({"UNAUTHENTICATED", "PERMISSION_DENIED"})

#: Device traits that publish events, in the order they appear in constants.
_EVENT_TRAITS: tuple[str, ...] = (
    constants.TRAIT_CAMERA_MOTION,
    constants.TRAIT_CAMERA_PERSON,
    constants.TRAIT_CAMERA_SOUND,
    constants.TRAIT_CAMERA_CLIP_PREVIEW,
    constants.TRAIT_DOORBELL_CHIME,
)

#: Cap on how much of a server error message is quoted back into an exception.
_MAX_SERVER_MESSAGE = 200


class SdmError(RuntimeError):
    """An SDM API call failed.

    Attributes mirror the documented taxonomy: ``status`` (HTTP), ``rpc_code``
    (``error.status`` from AIP-193), ``message`` and ``retryable``.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        rpc_code: str | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.rpc_code = rpc_code
        self.retryable = retryable

    def __repr__(self) -> str:  # noqa: D105
        return (
            f"<{type(self).__name__} status={self.status} rpc={self.rpc_code} "
            f"retryable={self.retryable}>"
        )


class SdmAuthError(SdmError):
    """HTTP 401/403 — ``UNAUTHENTICATED`` or ``PERMISSION_DENIED``."""


class SdmRateLimited(SdmError):
    """HTTP 429 / ``RESOURCE_EXHAUSTED`` — the server rejected us for quota.

    Raised only *after* ``limiter.penalize(...)`` has recorded the backoff, so
    the caller's next :meth:`SdmClient` call is refused locally rather than
    hammering the API again.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        rpc_code: str | None = None,
        retry_at: float | None = None,
    ) -> None:
        super().__init__(message, status=status, rpc_code=rpc_code, retryable=True)
        self.retry_at = retry_at


class SdmThrottled(RuntimeError):
    """LOCAL refusal: our own quota budget is not yet available.

    No HTTP request was made. ``retry_at`` is the absolute clock value (same
    clock the client was constructed with) at which a call of this shape becomes
    allowed. This is the mechanism that makes a burst structurally impossible.
    """

    def __init__(
        self,
        message: str,
        *,
        retry_at: float,
        method: str | None = None,
        device_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.retry_at = float(retry_at)
        self.method = method
        #: NOTE: kept in memory for the poller's scheduling only — never wired.
        self.device_id = device_id

    def __repr__(self) -> str:  # noqa: D105
        return f"<SdmThrottled method={self.method} retryAt={self.retry_at:.3f}>"


# ── device model ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class NestDevice:
    """One entry from ``devices.list`` / ``devices.get``.

    ``name`` is the full resource name
    ``enterprises/{project-id}/devices/{device-id}``; ``device_id`` is its last
    segment. Both are site identifiers and stay off the public wire.
    """

    name: str
    device_id: str
    type: str
    traits: dict[str, Any] = field(default_factory=dict)
    parent_relations: tuple[dict[str, Any], ...] = ()

    @classmethod
    def from_api(cls, obj: Mapping[str, Any] | Any) -> "NestDevice":
        """Parse tolerantly: unknown keys ignored, missing keys defaulted.

        A malformed payload yields a device with empty fields rather than an
        exception — a single bad entry must never take down a poll cycle.
        """
        if not isinstance(obj, Mapping):
            return cls(name="", device_id="", type="", traits={}, parent_relations=())
        name = obj.get("name")
        name = name if isinstance(name, str) else ""
        dev_type = obj.get("type")
        dev_type = dev_type if isinstance(dev_type, str) else ""
        traits = obj.get("traits")
        traits = dict(traits) if isinstance(traits, Mapping) else {}
        relations_raw = obj.get("parentRelations")
        relations: tuple[dict[str, Any], ...] = ()
        if isinstance(relations_raw, Sequence) and not isinstance(
            relations_raw, (str, bytes)
        ):
            relations = tuple(
                dict(rel) for rel in relations_raw if isinstance(rel, Mapping)
            )
        return cls(
            name=name,
            device_id=device_id_from_name(name),
            type=dev_type,
            traits=traits,
            parent_relations=relations,
        )

    @property
    def is_camera_like(self) -> bool:
        """CAMERA / DOORBELL / DISPLAY, or any device carrying a camera trait."""
        if self.type in constants.CAMERA_LIKE_TYPES:
            return True
        return any(trait in constants.CAMERA_TRAITS for trait in self.traits)

    @property
    def connectivity(self) -> str | None:
        """``"ONLINE"`` / ``"OFFLINE"`` from the Connectivity trait, else ``None``."""
        trait = self.traits.get(constants.TRAIT_CONNECTIVITY)
        if not isinstance(trait, Mapping):
            return None
        status = trait.get("status")
        return status if isinstance(status, str) else None

    def supports(self, trait: str) -> bool:
        """True when the device reports ``trait``."""
        return trait in self.traits

    def event_traits(self) -> tuple[str, ...]:
        """The event-publishing traits this device carries, in constant order."""
        return tuple(trait for trait in _EVENT_TRAITS if trait in self.traits)


def device_id_from_name(name: str) -> str:
    """Last path segment of a device resource name (``""`` when absent).

    Accepts a bare id too, so callers may pass either form.
    """
    if not isinstance(name, str) or not name:
        return ""
    return name.rstrip("/").rsplit("/", 1)[-1]


# ── client ───────────────────────────────────────────────────────────────────


class SdmClient:
    """SDM REST calls, each gated by the injected quota limiter.

    ``limiter`` is duck-typed against
    :class:`iot_asp_autoroute.nest.rate_limit.SdmRateLimiter`: it must provide
    ``try_acquire``, ``next_allowed_at`` and ``penalize`` with the keyword
    signature in NEST_DESIGN.md. It is *not* imported here, so this module stays
    independently testable with a fake.
    """

    def __init__(
        self,
        auth: Any,
        *,
        da_project_id: str,
        limiter: Any,
        transport: Transport | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not da_project_id or not str(da_project_id).strip():
            raise ValueError("da_project_id is required (the Device Access project id)")
        self._auth = auth
        self._project = str(da_project_id).strip()
        self._limiter = limiter
        self._transport: Transport = transport or urllib_transport
        self._clock = clock
        #: consecutive RESOURCE_EXHAUSTED count per call shape, for backoff.
        self._penalty_attempts: dict[tuple[str, str | None], int] = {}
        self._calls = 0

    # ── public API ───────────────────────────────────────────────────────────

    def list_devices(self, *, now: float | None = None) -> list[NestDevice]:
        """``GET enterprises/{project-id}/devices``.

        Pagination is deliberately NOT followed: chasing ``nextPageToken`` inside
        one call would spend several quota units for one limiter acquisition,
        which is exactly the burst this design forbids. The fleet is small enough
        that one page suffices; if that ever stops being true it becomes a
        scheduled second action in ``poller``, not a loop here.
        """
        url = f"{constants.SDM_API_BASE}/enterprises/{self._project}/devices"
        payload = self._call(
            constants.METHOD_DEVICES_LIST, "GET", url, now=now
        )
        raw = payload.get("devices")
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            return []
        return [NestDevice.from_api(obj) for obj in raw]

    def get_device(
        self,
        device_id: str,
        *,
        device_type: str | None = None,
        now: float | None = None,
    ) -> NestDevice:
        """``GET enterprises/{project-id}/devices/{device-id}``."""
        did = device_id_from_name(device_id)
        if not did:
            raise ValueError("device_id is required")
        url = (
            f"{constants.SDM_API_BASE}/enterprises/{self._project}/devices/"
            f"{urllib.parse.quote(did, safe='')}"
        )
        payload = self._call(
            constants.METHOD_DEVICES_GET,
            "GET",
            url,
            device_id=did,
            device_type=device_type,
            now=now,
        )
        return NestDevice.from_api(payload)

    def execute_command(
        self,
        device_id: str,
        command: str,
        params: Mapping[str, Any] | None = None,
        *,
        device_type: str | None = None,
        now: float | None = None,
    ) -> dict[str, Any]:
        """``POST enterprises/{project-id}/devices/{device-id}:executeCommand``.

        Body is ``{"command": ..., "params": {...}}``. Note the separate
        per-device trait-command budget of
        :data:`constants.TRAIT_COMMAND_QPM` QPM — the limiter owns that; this
        method only asks.
        """
        did = device_id_from_name(device_id)
        if not did:
            raise ValueError("device_id is required")
        if not command or not isinstance(command, str):
            raise ValueError("command is required")
        url = (
            f"{constants.SDM_API_BASE}/enterprises/{self._project}/devices/"
            f"{urllib.parse.quote(did, safe='')}:executeCommand"
        )
        body = json.dumps(
            {"command": command, "params": dict(params or {})}, sort_keys=True
        ).encode("utf-8")
        return self._call(
            constants.METHOD_DEVICES_EXECUTE_COMMAND,
            "POST",
            url,
            device_id=did,
            device_type=device_type,
            now=now,
            body=body,
        )

    def download(
        self,
        url: str,
        *,
        bearer: str | None = None,
        basic: str | None = None,
    ) -> bytes:
        """Fetch a media URL with the ONE correct Authorization scheme.

        * ``basic=`` — the ``token`` returned beside a ``GenerateImage`` ``url``.
          The docs show ``Authorization: Basic <token>`` verbatim, and the image
          expires ``constants.EVENT_IMAGE_TTL_S`` (30 s) after the event.
        * ``bearer=`` — an OAuth access token, for a CameraClipPreview
          ``previewUrl`` (``Authorization: Bearer access-token``).

        Exactly one must be given; passing both or neither raises ``ValueError``
        rather than guessing, because guessing wrong is a silent 403.

        Not limiter-gated: a media host is not an SDM API method and has no
        documented QPM on the project limits page. The call that *produced* the
        URL was already counted.
        """
        if bool(bearer) == bool(basic):
            raise ValueError(
                "download() needs exactly one of bearer= (CameraClipPreview "
                "previewUrl) or basic= (CameraEventImage GenerateImage token)"
            )
        scheme, token = ("Bearer", bearer) if bearer else ("Basic", basic)
        headers = {"Authorization": f"{scheme} {token}"}
        status, _headers, body = self._transport("GET", url, headers, None)
        if not 200 <= int(status) < 300:
            rpc = HTTP_TO_RPC.get(int(status), "UNKNOWN")
            raise SdmError(
                f"media download failed (HTTP {status}, {rpc})",
                status=int(status),
                rpc_code=rpc,
                retryable=rpc in RETRYABLE_RPC_CODES,
            )
        return body

    # ── health ───────────────────────────────────────────────────────────────

    def status(self) -> dict[str, Any]:
        """Health dict for ``poller.health()`` — counters only, no values."""
        out: dict[str, Any] = {
            "daProjectIdSet": bool(self._project),
            "calls": self._calls,
            "penaltyAttempts": {
                f"{m}:{'device' if d else 'project'}": n
                for (m, d), n in sorted(self._penalty_attempts.items())
            },
        }
        snapshot = getattr(self._limiter, "snapshot", None)
        if callable(snapshot):
            try:
                out["limiter"] = snapshot(float(self._clock()))
            except Exception:  # noqa: BLE001 - health must never raise
                out["limiter"] = None
        return out

    def __repr__(self) -> str:  # noqa: D105 - never leak project id or tokens
        return f"<SdmClient daProjectIdSet={bool(self._project)} calls={self._calls}>"

    __str__ = __repr__

    # ── internals ────────────────────────────────────────────────────────────

    def _call(
        self,
        method: str,
        http_method: str,
        url: str,
        *,
        device_id: str | None = None,
        device_type: str | None = None,
        now: float | None = None,
        body: bytes | None = None,
    ) -> dict[str, Any]:
        """Limiter → token → one HTTP round trip → parsed payload or raise."""
        at = float(self._clock()) if now is None else float(now)
        shape = (method, device_id)

        if not self._limiter.try_acquire(
            method, device_id=device_id, device_type=device_type, now=at
        ):
            retry_at = float(
                self._limiter.next_allowed_at(
                    method, device_id=device_id, device_type=device_type, now=at
                )
            )
            raise SdmThrottled(
                f"{method} budget not available yet; retry at {retry_at:.3f}",
                retry_at=retry_at,
                method=method,
                device_id=device_id,
            )

        headers = {
            "Authorization": f"Bearer {self._auth.access_token()}",
            "Accept": "application/json",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"

        status, _resp_headers, raw = self._transport(http_method, url, headers, body)
        status = int(status)
        self._calls += 1
        payload = _loads(raw)

        if 200 <= status < 300:
            self._penalty_attempts.pop(shape, None)
            return payload

        rpc_code, server_message = _classify(status, payload)

        if rpc_code == constants.RATE_LIMIT_RPC_CODE or status == (
            constants.RATE_LIMIT_HTTP_STATUS
        ):
            attempt = self._penalty_attempts.get(shape, 0) + 1
            self._penalty_attempts[shape] = attempt
            retry_at = _safe_penalize(
                self._limiter,
                method,
                device_id=device_id,
                device_type=device_type,
                now=at,
                attempt=attempt,
            )
            raise SdmRateLimited(
                f"{method} rate limited by SDM (HTTP {status}, "
                f"{constants.RATE_LIMIT_RPC_CODE}, attempt {attempt}): "
                f"{server_message}",
                status=status,
                rpc_code=constants.RATE_LIMIT_RPC_CODE,
                retry_at=retry_at,
            )

        retryable = rpc_code in RETRYABLE_RPC_CODES
        message = f"{method} failed (HTTP {status}, {rpc_code}): {server_message}"
        if rpc_code in _AUTH_RPC_CODES:
            raise SdmAuthError(
                message + " — re-check the Device Access OAuth consent and the "
                f"secret NAMES {', '.join(constants.SECRET_NAMES)}",
                status=status,
                rpc_code=rpc_code,
                retryable=retryable,
            )
        raise SdmError(
            message, status=status, rpc_code=rpc_code, retryable=retryable
        )


def _safe_penalize(
    limiter: Any,
    method: str,
    *,
    device_id: str | None,
    device_type: str | None,
    now: float,
    attempt: int,
) -> float | None:
    """Call ``limiter.penalize`` and return its deadline; never raise."""
    penalize = getattr(limiter, "penalize", None)
    if not callable(penalize):
        return None
    try:
        return float(
            penalize(
                method,
                device_id=device_id,
                device_type=device_type,
                now=now,
                attempt=attempt,
            )
        )
    except Exception:  # noqa: BLE001 - the 429 itself is the important signal
        return None


def _classify(status: int, payload: Mapping[str, Any]) -> tuple[str, str]:
    """``(rpc_code, short server message)`` from an AIP-193 error body.

    Falls back to :data:`HTTP_TO_RPC` when the body is missing or malformed.
    The server message is truncated and stripped of newlines before it reaches
    an exception, so a hostile body cannot smuggle structure into a log line.
    """
    err = payload.get("error") if isinstance(payload, Mapping) else None
    rpc_code = ""
    message = ""
    if isinstance(err, Mapping):
        raw_status = err.get("status")
        if isinstance(raw_status, str) and raw_status.strip():
            rpc_code = raw_status.strip()
        raw_message = err.get("message")
        if isinstance(raw_message, str):
            message = raw_message
    if not rpc_code:
        rpc_code = HTTP_TO_RPC.get(int(status), "UNKNOWN")
    clean = " ".join(message.split())[:_MAX_SERVER_MESSAGE]
    return rpc_code, clean or "(no message)"


def _loads(raw: bytes | str | None) -> dict[str, Any]:
    """Parse a JSON object, tolerating empty / malformed / non-object bodies."""
    if not raw:
        return {}
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            return {}
    try:
        obj = json.loads(raw)
    except Exception:  # noqa: BLE001 - a non-JSON body is data, not a crash
        return {}
    return obj if isinstance(obj, dict) else {}
