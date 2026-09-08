"""OAuth 2.0 refresh-token exchange for the Smart Device Management (SDM) API.

Issue #85 (M8 Nest checklist), spec ``docs/specs/85-nest-google-home-integration.md``.

What this module does and nothing else: turn the four Device Access **secret
names** in :mod:`iot_asp_autoroute.nest.constants` into a short-lived bearer
access token, caching it until it is within ``skew_s`` of expiry.

Verified API facts (every claim carries the page that states it):

* The refresh-token grant is an HTTP ``POST`` of a **form-encoded** body with
  exactly ``grant_type=refresh_token``, ``client_id``, ``client_secret`` and
  ``refresh_token`` — https://developers.google.com/nest/device-access/authorize
* The success body is JSON with ``access_token``, ``expires_in`` (seconds,
  ``3599`` in the documented example), ``scope`` and ``token_type: "Bearer"`` —
  same page.
* Authorization is *not* complete until the first ``devices.list`` call succeeds
  with the new token ("This call is required as part of authorization"), which is
  why :data:`constants.REQUIRES_FIRST_LIST_CALL` exists — same page.
* A refresh token issued to a **non-production** OAuth client expires after
  7 days, after which the grant fails and the owner must re-consent through the
  Partner Connections Manager —
  https://developers.google.com/nest/device-access/reference/errors/authorization
  (that page also documents ``Invalid client`` for a wrong client secret and
  ``Redirect uri mismatch``).

Endpoint note (deliberate, do not "fix"): the authorize page above prints the
legacy endpoint ``https://www.googleapis.com/oauth2/v4/token``. The frozen
:data:`constants.SDM_TOKEN_ENDPOINT` is the current Google Identity endpoint
``https://oauth2.googleapis.com/token``. ``constants.py`` is the single source of
truth (NEST_DESIGN.md), so this module never re-derives or overrides it.

House rules honoured here:

* stdlib only; no ``google-*`` import at any depth.
* All HTTP goes through an **injectable transport**
  ``(method, url, headers, body) -> (status, headers, body_bytes)``, so every
  test is offline. The default transport is a thin ``urllib.request`` shim.
* No blocking sleeps and no retry loops — the caller (the poller) owns time.
* **Secrets by name only** (CLAUDE.md #10): no credential value ever reaches a
  ``repr``, ``str``, log line or exception message. OAuth error codes echoed back
  from Google are sanitised to ``[a-z_]`` before they are put in a message, so a
  server that reflected a token could still not leak it through this module.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, ClassVar, Mapping

from . import constants

__all__ = [
    "NestConfigError",
    "NestAuthError",
    "NestSecrets",
    "NestAuth",
    "Transport",
    "urllib_transport",
]

#: ``(method, url, headers, body) -> (status, headers, body_bytes)``.
Transport = Callable[
    [str, str, Mapping[str, str], "bytes | None"],
    "tuple[int, dict[str, str], bytes]",
]

#: Default request timeout for the built-in transport (seconds).
DEFAULT_TIMEOUT_S: float = 20.0

#: A response without a usable ``expires_in`` is treated as already expired, so
#: the next :meth:`NestAuth.access_token` refreshes rather than trusting a token
#: of unknown lifetime. Fail-safe, and never a burst: one refresh per call.
_UNKNOWN_EXPIRY_S: float = 0.0

_SAFE_ERROR_RE = re.compile(r"[^a-z_]")

#: Remediation text for a dead refresh token. Names only — never a value.
_REAUTH_HINT = (
    "the Device Access refresh token is no longer valid (a non-production OAuth "
    "client expires it after 7 days). Re-consent as the Device Access owner "
    f"through the Partner Connections Manager URL built from "
    f"constants.PCM_AUTH_URL_TEMPLATE, then store the new value under the secret "
    f"NAME {constants.ENV_REFRESH_TOKEN} (never in git). Console: "
    f"{constants.DEVICE_ACCESS_CONSOLE}"
)


class NestConfigError(RuntimeError):
    """A required Device Access environment variable is missing or blank.

    The message names the **environment variable name** only — never a value,
    never a partial value, never a length.
    """


class NestAuthError(RuntimeError):
    """The token endpoint refused the refresh-token grant.

    ``oauth_error`` is the sanitised OAuth error code (for example
    ``invalid_grant``); ``status`` is the HTTP status of the token response.
    """

    def __init__(
        self,
        message: str,
        *,
        oauth_error: str | None = None,
        status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.oauth_error = oauth_error
        self.status = status


def _sanitize_error_code(value: Any) -> str:
    """Reduce a server-supplied OAuth error code to a safe ``[a-z_]`` token.

    Credential material (refresh tokens, client secrets, client ids) contains
    digits, ``.``, ``-``, ``/`` and mixed case, none of which survive this
    filter. That makes it structurally impossible for this module to echo a
    secret out of an error body.
    """
    if not isinstance(value, str):
        return "unknown_error"
    cleaned = _SAFE_ERROR_RE.sub("", value.lower())[:40]
    return cleaned or "unknown_error"


def urllib_transport(
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: bytes | None = None,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> tuple[int, dict[str, str], bytes]:
    """Default transport: one ``urllib.request`` round trip, no retries.

    Returns ``(status, headers, body_bytes)`` for **every** outcome including
    4xx/5xx — an HTTP error status is data here, not an exception, so callers
    can classify it. Never logs the request headers (they carry the bearer
    token) and never raises with the body in the message.
    """
    req = urllib.request.Request(url, data=body, method=method.upper())
    for key, value in headers.items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            return int(resp.status), dict(resp.headers.items()), resp.read()
    except urllib.error.HTTPError as exc:  # documented non-2xx path
        payload = exc.read() if hasattr(exc, "read") else b""
        return int(exc.code), dict(exc.headers.items() if exc.headers else {}), payload


@dataclass(frozen=True, repr=False)
class NestSecrets:
    """The four Device Access credentials, held in memory only.

    ``da_project_id`` is the Device Access **project id** (a UUID from
    https://console.nest.google.com/device-access) and is *not* the Google Cloud
    project id — see ``constants.PCM_AUTH_URL_TEMPLATE``.

    ``__repr__`` reports presence, never values (CLAUDE.md #10).
    """

    da_project_id: str
    client_id: str
    client_secret: str
    refresh_token: str

    #: env var name → dataclass field name. ``ClassVar`` so it is NOT a field.
    _ENV_FIELDS: ClassVar[tuple[tuple[str, str], ...]] = (
        (constants.ENV_DA_PROJECT_ID, "da_project_id"),
        (constants.ENV_OAUTH_CLIENT_ID, "client_id"),
        (constants.ENV_OAUTH_CLIENT_SECRET, "client_secret"),
        (constants.ENV_REFRESH_TOKEN, "refresh_token"),
    )

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "NestSecrets":
        """Build from a mapping (defaults to ``os.environ``).

        Raises :class:`NestConfigError` naming every missing or blank variable —
        by NAME, sorted, and nothing else.
        """
        if env is None:
            import os

            env = os.environ
        values: dict[str, str] = {}
        missing: list[str] = []
        for env_name, field in cls._ENV_FIELDS:
            raw = env.get(env_name)
            if raw is None or not str(raw).strip():
                missing.append(env_name)
            else:
                values[field] = str(raw).strip()
        if missing:
            raise NestConfigError(
                "missing Device Access environment variable(s): "
                + ", ".join(sorted(missing))
                + " (set the NAMES only; values live in Secret Manager / 1Password)"
            )
        return cls(**values)

    def __repr__(self) -> str:  # noqa: D105 - redaction is the whole point
        def mark(value: str) -> str:
            return "set" if value else "unset"

        return (
            "<NestSecrets"
            f" daProjectId={mark(self.da_project_id)}"
            f" clientId={mark(self.client_id)}"
            f" clientSecret={mark(self.client_secret)}"
            f" refreshToken={mark(self.refresh_token)}>"
        )

    __str__ = __repr__

    def status(self) -> dict[str, bool]:
        """Presence map for health output — booleans only, never values."""
        return {
            "daProjectId": bool(self.da_project_id),
            "clientId": bool(self.client_id),
            "clientSecret": bool(self.client_secret),
            "refreshToken": bool(self.refresh_token),
        }


class NestAuth:
    """Cached access-token provider for the SDM API.

    ``access_token()`` returns the cached token until it is within ``skew_s`` of
    expiry; only then does it issue exactly one refresh request. There is no
    retry loop and no sleep — a failed refresh raises and the poller decides.
    """

    def __init__(
        self,
        secrets: NestSecrets,
        *,
        transport: Transport | None = None,
        clock: Callable[[], float] = time.time,
        skew_s: float = 60.0,
    ) -> None:
        if skew_s < 0:
            raise ValueError(f"skew_s must be >= 0, got {skew_s}")
        self._secrets = secrets
        self._transport: Transport = transport or urllib_transport
        self._clock = clock
        self._skew_s = float(skew_s)
        self._token: str | None = None
        self._expires_at: float = 0.0
        self._refreshes = 0

    # ── token lifecycle ──────────────────────────────────────────────────────

    def access_token(self) -> str:
        """Cached bearer token, refreshed only when within ``skew_s`` of expiry."""
        now = float(self._clock())
        if self._token is not None and now < (self._expires_at - self._skew_s):
            return self._token
        return self.force_refresh()

    def force_refresh(self) -> str:
        """Unconditionally exchange the refresh token for a new access token."""
        body = urllib.parse.urlencode(
            {
                "grant_type": "refresh_token",
                "client_id": self._secrets.client_id,
                "client_secret": self._secrets.client_secret,
                "refresh_token": self._secrets.refresh_token,
            }
        ).encode("utf-8")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        status, _resp_headers, raw = self._transport(
            "POST", constants.SDM_TOKEN_ENDPOINT, headers, body
        )
        payload = _loads(raw)

        if int(status) != 200 or "access_token" not in payload:
            raise self._auth_error(int(status), payload)

        token = payload.get("access_token")
        if not isinstance(token, str) or not token:
            raise NestAuthError(
                "token endpoint returned no usable access_token", status=int(status)
            )

        expires_in = _coerce_float(payload.get("expires_in"), _UNKNOWN_EXPIRY_S)
        now = float(self._clock())
        self._token = token
        self._expires_at = now + max(0.0, expires_in)
        self._refreshes += 1
        return token

    def _auth_error(self, status: int, payload: Mapping[str, Any]) -> NestAuthError:
        """Map a failed token response to a helpful, non-leaking exception."""
        code = _sanitize_error_code(payload.get("error"))
        if code == "invalid_grant":
            message = f"OAuth refresh rejected (invalid_grant): {_REAUTH_HINT}"
        elif code == "invalid_client":
            message = (
                "OAuth refresh rejected (invalid_client): the client id/secret pair "
                f"behind {constants.ENV_OAUTH_CLIENT_ID} / "
                f"{constants.ENV_OAUTH_CLIENT_SECRET} does not match the Device "
                "Access OAuth client"
            )
        else:
            message = (
                f"OAuth refresh failed (HTTP {status}, error={code}); check the "
                "Device Access OAuth client and the secret NAMES "
                + ", ".join(constants.SECRET_NAMES)
            )
        return NestAuthError(message, oauth_error=code, status=status)

    # ── introspection (never values) ─────────────────────────────────────────

    def status(self) -> dict[str, Any]:
        """Health dict: ``{"hasRefreshToken": bool, "expiresInS": int | None}``."""
        expires_in: int | None = None
        if self._token is not None:
            expires_in = int(max(0.0, self._expires_at - float(self._clock())))
        return {
            "hasRefreshToken": bool(self._secrets.refresh_token),
            "expiresInS": expires_in,
            "hasCachedToken": self._token is not None,
            "refreshes": self._refreshes,
            "skewS": self._skew_s,
        }

    def __repr__(self) -> str:  # noqa: D105 - redaction is the whole point
        state = self.status()
        return (
            "<NestAuth"
            f" hasRefreshToken={state['hasRefreshToken']}"
            f" cachedToken={state['hasCachedToken']}"
            f" expiresInS={state['expiresInS']}"
            f" refreshes={state['refreshes']}>"
        )

    __str__ = __repr__


# ── tolerant helpers ─────────────────────────────────────────────────────────


def _loads(raw: bytes | str | None) -> dict[str, Any]:
    """Parse a JSON object, tolerating empty / malformed / non-object bodies."""
    if not raw:
        return {}
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8", "replace")
        except Exception:  # noqa: BLE001 - pragmatic; never re-raise body content
            return {}
    try:
        obj = json.loads(raw)
    except Exception:  # noqa: BLE001 - a non-JSON body is data, not a crash
        return {}
    return obj if isinstance(obj, dict) else {}


def _coerce_float(value: Any, default: float) -> float:
    """``float(value)`` or ``default`` — never raises."""
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
