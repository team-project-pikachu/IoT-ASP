"""Tests for iot_asp_autoroute.nest.auth + nest.sdm_client (#85) — offline.

Acceptance IDs NA-01 … NA-09 (auth) and NC-01 … NC-14 (client) from
docs/specs/85-nest-google-home-integration.md.

Everything here is deterministic: an injected clock, an injected transport that
records every request, and Google's own documentation placeholders
(``project-id``, ``device-id``, ``structure-id``) as fixtures. No network, no
sleeps, no real identifiers, no secret values.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = ROOT / "services" / "autoroute-adk"
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from iot_asp_autoroute.nest import auth as na  # noqa: E402
from iot_asp_autoroute.nest import constants as nc  # noqa: E402
from iot_asp_autoroute.nest import sdm_client as sc  # noqa: E402

# Documentation placeholders only (NEST_DESIGN.md #5).
PROJECT_ID = "project-id"
DEVICE_ID = "device-id"
STRUCTURE_ID = "structure-id"
DEVICE_NAME = f"enterprises/{PROJECT_ID}/devices/{DEVICE_ID}"

#: A single string that must never appear in any repr/str/exception. Mixed case
#: plus digits and punctuation, so it also survives the auth error sanitiser test.
SENTINEL = "Zx9-SENTINEL-DO-NOT-LEAK-9xZ"


# ── fakes ────────────────────────────────────────────────────────────────────


class FakeClock:
    """Monotonic-looking clock the test advances by hand."""

    def __init__(self, start: float = 1000.0) -> None:
        self.t = float(start)

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> float:
        self.t += float(dt)
        return self.t


class RecordingTransport:
    """Injected transport: replays queued responses, records every request."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.requests: list[dict] = []

    def __call__(self, method, url, headers, body=None):
        self.requests.append(
            {
                "method": method,
                "url": url,
                "headers": dict(headers),
                "body": body,
            }
        )
        if not self.responses:
            raise AssertionError(f"unexpected transport call: {method} {url}")
        status, payload = self.responses.pop(0)
        raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        return status, {"Content-Type": "application/json"}, raw

    @property
    def calls(self) -> int:
        return len(self.requests)


class FakeLimiter:
    """Duck-typed stand-in for rate_limit.SdmRateLimiter."""

    def __init__(self, *, allow: bool = True, next_at: float = 0.0) -> None:
        self.allow = allow
        self.next_at = next_at
        self.acquired: list[tuple] = []
        self.penalties: list[dict] = []

    def try_acquire(self, method, *, device_id=None, device_type=None, now):
        self.acquired.append((method, device_id, device_type, now))
        return self.allow

    def next_allowed_at(self, method, *, device_id=None, device_type=None, now):
        return now + self.next_at

    def penalize(self, method, *, device_id=None, device_type=None, now, attempt):
        self.penalties.append(
            {
                "method": method,
                "device_id": device_id,
                "device_type": device_type,
                "now": now,
                "attempt": attempt,
            }
        )
        return now + min(nc.BACKOFF_BASE_S**attempt, nc.BACKOFF_MAX_S)

    def snapshot(self, now):
        return {"now": now, "buckets": {}}


def token_response(access_token: str = "test-access-token", expires_in=3599):
    """Documented success body: access_token / expires_in / scope / token_type."""
    body = {
        "access_token": access_token,
        "expires_in": expires_in,
        "scope": nc.SDM_OAUTH_SCOPE,
        "token_type": "Bearer",
    }
    if expires_in is None:
        body.pop("expires_in")
    return 200, body


def make_secrets(**overrides) -> na.NestSecrets:
    values = {
        "da_project_id": PROJECT_ID,
        "client_id": "oauth2-client-id",
        "client_secret": "oauth2-client-secret",
        "refresh_token": "refresh-token",
    }
    values.update(overrides)
    return na.NestSecrets(**values)


def make_auth(transport=None, clock=None, skew_s=60.0):
    return na.NestAuth(
        make_secrets(),
        transport=transport or RecordingTransport([token_response()]),
        clock=clock or FakeClock(),
        skew_s=skew_s,
    )


def make_client(transport, *, limiter=None, clock=None, auth=None):
    clock = clock or FakeClock()
    return sc.SdmClient(
        auth or make_auth(RecordingTransport([token_response()] * 20), FakeClock()),
        da_project_id=PROJECT_ID,
        limiter=limiter or FakeLimiter(),
        transport=transport,
        clock=clock,
    )


# ── NA-01 stdlib-only import ─────────────────────────────────────────────────


def test_na01_modules_import_with_stdlib_only():
    """A fresh interpreter importing these modules pulls in no google-* module.

    Run in a subprocess so an unrelated test in the same session cannot pollute
    ``sys.modules`` and make this pass or fail by accident.
    """
    import subprocess

    # Measure the DELTA the nest modules add, not the absolute set. The parent package
    # `iot_asp_autoroute` soft-imports `.agent`, which legitimately pulls in google.adk
    # whenever ADK happens to be installed (see iot_asp_autoroute/__init__.py). Asserting
    # an empty absolute set therefore tests the parent's optional dependency rather than
    # this package's, and fails on any machine with `pip install google-adk` while passing
    # in CI, where requirements-dev.txt omits ADK. The property we actually care about is
    # that importing the nest modules adds no third-party module of its own.
    script = (
        "import sys\n"
        "import iot_asp_autoroute\n"  # parent first: its optional .agent import is not ours
        "before = set(sys.modules)\n"
        "import iot_asp_autoroute.nest.auth as a\n"
        "import iot_asp_autoroute.nest.sdm_client as c\n"
        "added = set(sys.modules) - before\n"
        "bad = sorted(m for m in added if m == 'google' or m.startswith('google.'))\n"
        "assert not bad, bad\n"
        "assert a.Transport is not None and c.SdmClient is not None\n"
        "print('OK')\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(PKG_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "OK"


# ── NA-02 from_env negative control: missing env var ─────────────────────────


def test_na02_from_env_names_missing_vars_only():
    with pytest.raises(na.NestConfigError) as exc:
        na.NestSecrets.from_env({})
    msg = str(exc.value)
    for name in nc.SECRET_NAMES:
        assert name in msg
    # names only — no hint of a value, no length, no partial
    assert "=" not in msg


@pytest.mark.parametrize("blank", ["", "   ", "\t\n"])
def test_na02b_blank_value_counts_as_missing(blank):
    env = {
        nc.ENV_DA_PROJECT_ID: PROJECT_ID,
        nc.ENV_OAUTH_CLIENT_ID: "oauth2-client-id",
        nc.ENV_OAUTH_CLIENT_SECRET: "oauth2-client-secret",
        nc.ENV_REFRESH_TOKEN: blank,
    }
    with pytest.raises(na.NestConfigError) as exc:
        na.NestSecrets.from_env(env)
    assert nc.ENV_REFRESH_TOKEN in str(exc.value)
    assert nc.ENV_DA_PROJECT_ID not in str(exc.value)


def test_na02c_from_env_happy_path_strips_whitespace():
    env = {
        nc.ENV_DA_PROJECT_ID: f"  {PROJECT_ID}  ",
        nc.ENV_OAUTH_CLIENT_ID: "oauth2-client-id",
        nc.ENV_OAUTH_CLIENT_SECRET: "oauth2-client-secret",
        nc.ENV_REFRESH_TOKEN: "refresh-token",
    }
    secrets = na.NestSecrets.from_env(env)
    assert secrets.da_project_id == PROJECT_ID
    assert secrets.status() == {
        "daProjectId": True,
        "clientId": True,
        "clientSecret": True,
        "refreshToken": True,
    }


def test_na02d_env_fields_is_classvar_not_a_dataclass_field():
    """_ENV_FIELDS must not become a 5th constructor argument."""
    import dataclasses

    names = {f.name for f in dataclasses.fields(na.NestSecrets)}
    assert names == {"da_project_id", "client_id", "client_secret", "refresh_token"}


# ── NA-03 token exchange uses the documented form grant ──────────────────────


def test_na03_refresh_posts_documented_form_body():
    tr = RecordingTransport([token_response("first-token")])
    auth = na.NestAuth(make_secrets(), transport=tr, clock=FakeClock())
    assert auth.access_token() == "first-token"

    req = tr.requests[0]
    assert req["method"] == "POST"
    assert req["url"] == nc.SDM_TOKEN_ENDPOINT
    assert req["headers"]["Content-Type"] == "application/x-www-form-urlencoded"

    from urllib.parse import parse_qs

    form = parse_qs(req["body"].decode())
    assert form["grant_type"] == ["refresh_token"]
    assert set(form) == {"grant_type", "client_id", "client_secret", "refresh_token"}


# ── NA-04 cache: a second call inside the window issues NO transport call ────


def test_na04_cached_token_makes_no_second_transport_call():
    clock = FakeClock(1000.0)
    tr = RecordingTransport([token_response("tok-1", expires_in=3599)])
    auth = na.NestAuth(make_secrets(), transport=tr, clock=clock, skew_s=60.0)

    assert auth.access_token() == "tok-1"
    assert tr.calls == 1

    clock.advance(3000.0)  # well inside 3599 - 60
    assert auth.access_token() == "tok-1"
    assert tr.calls == 1, "cached token must not re-hit the token endpoint"


def test_na04b_refresh_happens_only_inside_the_skew_window():
    clock = FakeClock(1000.0)
    tr = RecordingTransport(
        [token_response("tok-1", expires_in=100), token_response("tok-2", 3599)]
    )
    auth = na.NestAuth(make_secrets(), transport=tr, clock=clock, skew_s=60.0)
    assert auth.access_token() == "tok-1"

    clock.advance(39.0)  # now 1039; expiry 1100, skew boundary 1040 -> still cached
    assert auth.access_token() == "tok-1"
    assert tr.calls == 1

    clock.advance(2.0)  # now 1041 >= 1040 -> refresh
    assert auth.access_token() == "tok-2"
    assert tr.calls == 2


def test_na04c_force_refresh_always_calls_transport():
    tr = RecordingTransport([token_response("a"), token_response("b")])
    auth = na.NestAuth(make_secrets(), transport=tr, clock=FakeClock())
    assert auth.access_token() == "a"
    assert auth.force_refresh() == "b"
    assert tr.calls == 2


def test_na04d_missing_expires_in_is_treated_as_expired():
    """Fail-safe: an unknown lifetime must not be trusted (one refresh per call)."""
    clock = FakeClock()
    tr = RecordingTransport([token_response("a", None), token_response("b", None)])
    auth = na.NestAuth(make_secrets(), transport=tr, clock=clock)
    assert auth.access_token() == "a"
    assert auth.access_token() == "b"
    assert tr.calls == 2


# ── NA-05 negative control: invalid_grant ────────────────────────────────────


def test_na05_invalid_grant_raises_helpful_non_leaking_error():
    tr = RecordingTransport(
        [(400, {"error": "invalid_grant", "error_description": "Token has been expired"})]
    )
    auth = na.NestAuth(make_secrets(), transport=tr, clock=FakeClock())
    with pytest.raises(na.NestAuthError) as exc:
        auth.access_token()

    msg = str(exc.value)
    assert exc.value.oauth_error == "invalid_grant"
    assert exc.value.status == 400
    # helpful: it names the remediation path and the secret NAME
    assert "Partner Connections Manager" in msg
    assert nc.ENV_REFRESH_TOKEN in msg
    assert nc.DEVICE_ACCESS_CONSOLE in msg
    # non-leaking: no credential value
    for value in ("oauth2-client-secret", "refresh-token"):
        assert value not in msg


def test_na05b_invalid_client_names_the_env_vars_not_values():
    tr = RecordingTransport([(401, {"error": "invalid_client"})])
    auth = na.NestAuth(make_secrets(), transport=tr, clock=FakeClock())
    with pytest.raises(na.NestAuthError) as exc:
        auth.access_token()
    assert nc.ENV_OAUTH_CLIENT_ID in str(exc.value)
    assert nc.ENV_OAUTH_CLIENT_SECRET in str(exc.value)


def test_na05c_error_code_is_sanitised_to_lowercase_letters():
    """A server that reflected a credential could still not leak it."""
    tr = RecordingTransport([(400, {"error": SENTINEL})])
    auth = na.NestAuth(make_secrets(), transport=tr, clock=FakeClock())
    with pytest.raises(na.NestAuthError) as exc:
        auth.access_token()
    assert SENTINEL not in str(exc.value)
    assert exc.value.oauth_error is not None
    assert exc.value.oauth_error.replace("_", "").isalpha()


def test_na05d_malformed_body_and_missing_token_still_raise_cleanly():
    tr = RecordingTransport([(200, b"<html>not json</html>")])
    auth = na.NestAuth(make_secrets(), transport=tr, clock=FakeClock())
    with pytest.raises(na.NestAuthError):
        auth.access_token()


# ── NA-06 redaction: the sentinel appears nowhere ────────────────────────────


def test_na06_sentinel_never_appears_in_any_repr_str_or_exception():
    env = {
        nc.ENV_DA_PROJECT_ID: SENTINEL,
        nc.ENV_OAUTH_CLIENT_ID: SENTINEL,
        nc.ENV_OAUTH_CLIENT_SECRET: SENTINEL,
        nc.ENV_REFRESH_TOKEN: SENTINEL,
    }
    secrets = na.NestSecrets.from_env(env)
    surfaces: list[str] = [repr(secrets), str(secrets), f"{secrets}", str(secrets.status())]

    clock = FakeClock()
    tr = RecordingTransport(
        [token_response(SENTINEL), (403, {"error": "invalid_grant"})]
    )
    auth = na.NestAuth(secrets, transport=tr, clock=clock, skew_s=0.0)
    surfaces += [repr(auth), str(auth), str(auth.status())]

    auth.access_token()  # caches a token equal to the sentinel
    surfaces += [repr(auth), str(auth), str(auth.status())]

    with pytest.raises(na.NestAuthError) as exc:
        auth.force_refresh()
    surfaces += [str(exc.value), repr(exc.value)]

    # and through the client, whose Authorization header carries the sentinel
    limiter = FakeLimiter()
    client_tr = RecordingTransport([(403, {"error": {"status": "PERMISSION_DENIED"}})])
    client = sc.SdmClient(
        na.NestAuth(
            secrets,
            transport=RecordingTransport([token_response(SENTINEL)]),
            clock=FakeClock(),
        ),
        da_project_id=SENTINEL,
        limiter=limiter,
        transport=client_tr,
        clock=FakeClock(),
    )
    surfaces += [repr(client), str(client), str(client.status())]
    with pytest.raises(sc.SdmAuthError) as sexc:
        client.list_devices()
    surfaces += [str(sexc.value), repr(sexc.value)]

    for surface in surfaces:
        assert SENTINEL not in surface, surface


def test_na06b_status_reports_presence_not_values():
    auth = make_auth()
    state = auth.status()
    assert state["hasRefreshToken"] is True
    assert state["expiresInS"] is None  # nothing fetched yet
    auth.access_token()
    assert isinstance(auth.status()["expiresInS"], int)


def test_na06c_negative_skew_refused():
    with pytest.raises(ValueError):
        na.NestAuth(make_secrets(), skew_s=-1.0)


# ── NC-01 REST paths match the documented API surface ────────────────────────


def test_nc01_list_devices_path_and_bearer_header():
    tr = RecordingTransport([(200, {"devices": []})])
    client = make_client(tr)
    assert client.list_devices() == []
    req = tr.requests[0]
    assert req["method"] == "GET"
    assert req["url"] == f"{nc.SDM_API_BASE}/enterprises/{PROJECT_ID}/devices"
    assert req["headers"]["Authorization"].startswith("Bearer ")


def test_nc01b_get_device_path():
    tr = RecordingTransport([(200, {"name": DEVICE_NAME, "type": nc.TYPE_CAMERA})])
    client = make_client(tr)
    dev = client.get_device(DEVICE_ID, device_type=nc.TYPE_CAMERA)
    assert (
        tr.requests[0]["url"]
        == f"{nc.SDM_API_BASE}/enterprises/{PROJECT_ID}/devices/{DEVICE_ID}"
    )
    assert dev.device_id == DEVICE_ID


def test_nc01c_get_device_accepts_a_full_resource_name():
    tr = RecordingTransport([(200, {"name": DEVICE_NAME, "type": nc.TYPE_CAMERA})])
    client = make_client(tr)
    client.get_device(DEVICE_NAME)
    assert tr.requests[0]["url"].endswith(f"/devices/{DEVICE_ID}")


def test_nc01d_execute_command_path_and_body():
    tr = RecordingTransport([(200, {"results": {"url": "https://x/y", "token": "t"}})])
    client = make_client(tr)
    out = client.execute_command(
        DEVICE_ID,
        nc.CMD_GENERATE_IMAGE,
        {"eventId": "event-id"},
        device_type=nc.TYPE_CAMERA,
    )
    req = tr.requests[0]
    assert req["method"] == "POST"
    assert req["url"] == (
        f"{nc.SDM_API_BASE}/enterprises/{PROJECT_ID}/devices/{DEVICE_ID}"
        ":executeCommand"
    )
    assert json.loads(req["body"].decode()) == {
        "command": nc.CMD_GENERATE_IMAGE,
        "params": {"eventId": "event-id"},
    }
    assert out["results"]["token"] == "t"


def test_nc01e_empty_device_id_and_command_refused():
    client = make_client(RecordingTransport([]))
    with pytest.raises(ValueError):
        client.get_device("")
    with pytest.raises(ValueError):
        client.execute_command(DEVICE_ID, "")
    with pytest.raises(ValueError):
        sc.SdmClient(
            make_auth(), da_project_id="  ", limiter=FakeLimiter(), transport=None
        )


# ── NC-02 the limiter is asked BEFORE every call ─────────────────────────────


def test_nc02_limiter_consulted_before_the_transport():
    limiter = FakeLimiter()
    tr = RecordingTransport([(200, {"devices": []})])
    client = make_client(tr, limiter=limiter, clock=FakeClock(500.0))
    client.list_devices()
    assert limiter.acquired == [(nc.METHOD_DEVICES_LIST, None, None, 500.0)]
    assert tr.calls == 1


def test_nc02b_device_shape_passed_to_the_limiter():
    limiter = FakeLimiter()
    tr = RecordingTransport([(200, {"name": DEVICE_NAME})])
    client = make_client(tr, limiter=limiter, clock=FakeClock(7.0))
    client.get_device(DEVICE_ID, device_type=nc.TYPE_DOORBELL)
    assert limiter.acquired == [
        (nc.METHOD_DEVICES_GET, DEVICE_ID, nc.TYPE_DOORBELL, 7.0)
    ]


# ── NC-03 negative control: throttled BEFORE the call ────────────────────────


def test_nc03_throttled_raises_with_a_future_retry_at_and_no_http():
    limiter = FakeLimiter(allow=False, next_at=36.0)
    tr = RecordingTransport([])  # any transport call would raise AssertionError
    clock = FakeClock(100.0)
    client = make_client(tr, limiter=limiter, clock=clock)

    with pytest.raises(sc.SdmThrottled) as exc:
        client.list_devices()

    assert exc.value.retry_at == pytest.approx(136.0)
    assert exc.value.retry_at > clock.t, "retry_at must be in the future"
    assert exc.value.method == nc.METHOD_DEVICES_LIST
    assert tr.calls == 0, "throttled means NO network call at all"
    assert limiter.penalties == [], "a local refusal is not a server penalty"


def test_nc03b_throttled_never_sleeps_or_retries():
    """The client must not loop: one refusal per invocation, deterministically."""
    limiter = FakeLimiter(allow=False, next_at=12.0)
    tr = RecordingTransport([])
    client = make_client(tr, limiter=limiter, clock=FakeClock(0.0))
    for _ in range(5):
        with pytest.raises(sc.SdmThrottled):
            client.list_devices()
    assert len(limiter.acquired) == 5  # exactly one acquire attempt per call
    assert tr.calls == 0


def test_nc03c_throttled_is_not_an_sdm_error_subclass():
    """A local refusal is a scheduling signal, not an API failure."""
    assert not issubclass(sc.SdmThrottled, sc.SdmError)
    assert issubclass(sc.SdmRateLimited, sc.SdmError)
    assert issubclass(sc.SdmAuthError, sc.SdmError)


# ── NC-04 negative control: HTTP 429 → penalize → SdmRateLimited ─────────────


def test_nc04_http_429_penalizes_then_raises():
    limiter = FakeLimiter()
    tr = RecordingTransport(
        [
            (
                429,
                {
                    "error": {
                        "code": 429,
                        "message": "Rate limited.",
                        "status": nc.RATE_LIMIT_RPC_CODE,
                    }
                },
            )
        ]
    )
    client = make_client(tr, limiter=limiter, clock=FakeClock(200.0))

    with pytest.raises(sc.SdmRateLimited) as exc:
        client.list_devices()

    assert exc.value.status == nc.RATE_LIMIT_HTTP_STATUS
    assert exc.value.rpc_code == nc.RATE_LIMIT_RPC_CODE
    assert exc.value.retryable is True
    assert exc.value.retry_at == pytest.approx(200.0 + nc.BACKOFF_BASE_S**1)
    assert limiter.penalties == [
        {
            "method": nc.METHOD_DEVICES_LIST,
            "device_id": None,
            "device_type": None,
            "now": 200.0,
            "attempt": 1,
        }
    ]


def test_nc04b_consecutive_429s_escalate_the_attempt_counter():
    limiter = FakeLimiter()
    tr = RecordingTransport([(429, {"error": {"status": nc.RATE_LIMIT_RPC_CODE}})] * 3)
    client = make_client(tr, limiter=limiter, clock=FakeClock(0.0))
    for _ in range(3):
        with pytest.raises(sc.SdmRateLimited):
            client.list_devices()
    assert [p["attempt"] for p in limiter.penalties] == [1, 2, 3]


def test_nc04c_a_success_resets_the_attempt_counter():
    limiter = FakeLimiter()
    tr = RecordingTransport(
        [
            (429, {"error": {"status": nc.RATE_LIMIT_RPC_CODE}}),
            (200, {"devices": []}),
            (429, {"error": {"status": nc.RATE_LIMIT_RPC_CODE}}),
        ]
    )
    client = make_client(tr, limiter=limiter, clock=FakeClock(0.0))
    with pytest.raises(sc.SdmRateLimited):
        client.list_devices()
    client.list_devices()
    with pytest.raises(sc.SdmRateLimited):
        client.list_devices()
    assert [p["attempt"] for p in limiter.penalties] == [1, 1]


def test_nc04d_bare_429_without_a_body_still_penalizes():
    limiter = FakeLimiter()
    tr = RecordingTransport([(429, b"")])
    client = make_client(tr, limiter=limiter, clock=FakeClock(0.0))
    with pytest.raises(sc.SdmRateLimited):
        client.list_devices()
    assert len(limiter.penalties) == 1


def test_nc04e_a_limiter_without_penalize_does_not_crash_the_client():
    class MinimalLimiter:
        def try_acquire(self, method, *, device_id=None, device_type=None, now):
            return True

        def next_allowed_at(self, method, *, device_id=None, device_type=None, now):
            return now

    tr = RecordingTransport([(429, {"error": {"status": nc.RATE_LIMIT_RPC_CODE}})])
    client = make_client(tr, limiter=MinimalLimiter(), clock=FakeClock(0.0))
    with pytest.raises(sc.SdmRateLimited) as exc:
        client.list_devices()
    assert exc.value.retry_at is None


# ── NC-05 error taxonomy is the documented one ───────────────────────────────


@pytest.mark.parametrize(
    "status,rpc_code,expected_type,retryable",
    [
        (400, "INVALID_ARGUMENT", sc.SdmError, False),
        (400, "FAILED_PRECONDITION", sc.SdmError, False),
        (401, "UNAUTHENTICATED", sc.SdmAuthError, False),
        (403, "PERMISSION_DENIED", sc.SdmAuthError, False),
        (404, "NOT_FOUND", sc.SdmError, False),
        (504, "DEADLINE_EXCEEDED", sc.SdmError, True),
    ],
)
def test_nc05_documented_error_codes_map_to_the_right_exception(
    status, rpc_code, expected_type, retryable
):
    tr = RecordingTransport([(status, {"error": {"status": rpc_code, "message": "x"}})])
    client = make_client(tr, clock=FakeClock(0.0))
    with pytest.raises(expected_type) as exc:
        client.list_devices()
    assert exc.value.status == status
    assert exc.value.rpc_code == rpc_code
    assert exc.value.retryable is retryable


def test_nc05b_http_to_rpc_matches_the_documented_table():
    """Codes transcribed from developers.google.com/.../reference/errors/api."""
    assert sc.HTTP_TO_RPC[400] == "INVALID_ARGUMENT"
    assert sc.HTTP_TO_RPC[403] == "PERMISSION_DENIED"
    assert sc.HTTP_TO_RPC[404] == "NOT_FOUND"
    assert sc.HTTP_TO_RPC[429] == nc.RATE_LIMIT_RPC_CODE == "RESOURCE_EXHAUSTED"
    assert sc.HTTP_TO_RPC[504] == "DEADLINE_EXCEEDED"
    # caller mistakes are never retried — retrying them only burns quota
    for code in ("INVALID_ARGUMENT", "FAILED_PRECONDITION", "NOT_FOUND"):
        assert code not in sc.RETRYABLE_RPC_CODES


def test_nc05c_unknown_status_falls_back_without_crashing():
    tr = RecordingTransport([(418, b"teapot")])
    client = make_client(tr, clock=FakeClock(0.0))
    with pytest.raises(sc.SdmError) as exc:
        client.list_devices()
    assert exc.value.rpc_code == "UNKNOWN"
    assert exc.value.retryable is False


def test_nc05d_server_message_is_truncated_and_flattened():
    long = "A" * 500 + "\nsecond line"
    tr = RecordingTransport([(400, {"error": {"status": "INVALID_ARGUMENT", "message": long}})])
    client = make_client(tr, clock=FakeClock(0.0))
    with pytest.raises(sc.SdmError) as exc:
        client.list_devices()
    assert "\n" not in str(exc.value)
    assert len(str(exc.value)) < 400


# ── NC-06 negative control: malformed device payloads parse tolerantly ───────


def test_nc06_malformed_device_payload_is_parsed_tolerantly():
    tr = RecordingTransport(
        [
            (
                200,
                {
                    "devices": [
                        {"name": DEVICE_NAME, "type": nc.TYPE_CAMERA},
                        {},  # no name, no type
                        {"name": 42, "type": None, "traits": "not-a-dict"},
                        {"name": DEVICE_NAME, "parentRelations": "not-a-list"},
                        {"name": DEVICE_NAME, "parentRelations": ["junk", {"parent": "p"}]},
                        "a bare string, not an object",
                        None,
                    ]
                },
            )
        ]
    )
    client = make_client(tr, clock=FakeClock(0.0))
    devices = client.list_devices()
    assert len(devices) == 7
    assert devices[0].device_id == DEVICE_ID
    assert devices[1].name == "" and devices[1].traits == {}
    assert devices[2].name == "" and devices[2].type == "" and devices[2].traits == {}
    assert devices[3].parent_relations == ()
    assert devices[4].parent_relations == ({"parent": "p"},)
    assert devices[5].device_id == ""
    assert devices[6].device_id == ""


def test_nc06b_list_devices_tolerates_a_missing_or_wrong_devices_key():
    for payload in ({}, {"devices": None}, {"devices": "nope"}, {"devices": {}}):
        tr = RecordingTransport([(200, payload)])
        client = make_client(tr, clock=FakeClock(0.0))
        assert client.list_devices() == []


def test_nc06c_non_json_success_body_yields_an_empty_device():
    tr = RecordingTransport([(200, b"<html/>")])
    client = make_client(tr, clock=FakeClock(0.0))
    dev = client.get_device(DEVICE_ID)
    assert dev.name == "" and dev.device_id == ""


# ── NC-07 NestDevice semantics ───────────────────────────────────────────────


def test_nc07_device_traits_and_connectivity():
    dev = sc.NestDevice.from_api(
        {
            "name": DEVICE_NAME,
            "type": nc.TYPE_DOORBELL,
            "traits": {
                nc.TRAIT_CONNECTIVITY: {"status": "ONLINE"},
                nc.TRAIT_CAMERA_SOUND: {},
                nc.TRAIT_DOORBELL_CHIME: {},
                nc.TRAIT_CAMERA_MOTION: {},
            },
            "parentRelations": [
                {
                    "parent": (
                        f"enterprises/{PROJECT_ID}/structures/{STRUCTURE_ID}"
                        "/rooms/room-id"
                    ),
                    "displayName": "Lobby",
                }
            ],
        }
    )
    assert dev.is_camera_like is True
    assert dev.connectivity == "ONLINE"
    assert dev.supports(nc.TRAIT_CAMERA_SOUND) is True
    assert dev.supports(nc.TRAIT_CAMERA_LIVE_STREAM) is False
    assert dev.event_traits() == (
        nc.TRAIT_CAMERA_MOTION,
        nc.TRAIT_CAMERA_SOUND,
        nc.TRAIT_DOORBELL_CHIME,
    )
    assert dev.parent_relations[0]["displayName"] == "Lobby"


def test_nc07b_connectivity_none_when_trait_missing_or_malformed():
    assert sc.NestDevice.from_api({"name": DEVICE_NAME}).connectivity is None
    bad = sc.NestDevice.from_api(
        {"name": DEVICE_NAME, "traits": {nc.TRAIT_CONNECTIVITY: "OFFLINE"}}
    )
    assert bad.connectivity is None
    numeric = sc.NestDevice.from_api(
        {"name": DEVICE_NAME, "traits": {nc.TRAIT_CONNECTIVITY: {"status": 1}}}
    )
    assert numeric.connectivity is None


def test_nc07c_camera_like_by_trait_even_with_an_unknown_type():
    dev = sc.NestDevice.from_api(
        {"name": DEVICE_NAME, "type": "sdm.devices.types.SOMETHING_NEW",
         "traits": {nc.TRAIT_CAMERA_CLIP_PREVIEW: {}}}
    )
    assert dev.is_camera_like is True
    thermostat = sc.NestDevice.from_api(
        {"name": DEVICE_NAME, "type": nc.TYPE_THERMOSTAT, "traits": {}}
    )
    assert thermostat.is_camera_like is False


def test_nc07d_device_id_from_name():
    assert sc.device_id_from_name(DEVICE_NAME) == DEVICE_ID
    assert sc.device_id_from_name(DEVICE_ID) == DEVICE_ID
    assert sc.device_id_from_name("") == ""
    assert sc.device_id_from_name(None) == ""  # type: ignore[arg-type]
    assert sc.device_id_from_name(f"{DEVICE_NAME}/") == DEVICE_ID


# ── NC-08 the download-auth trap: Basic for images, Bearer for clips ─────────


def test_nc08_event_image_download_uses_authorization_basic():
    """GenerateImage returns {url, token}; the token is a BASIC credential."""
    tr = RecordingTransport([(200, b"\x89PNG-bytes")])
    client = make_client(tr, clock=FakeClock(0.0))
    data = client.download("https://domain/sdm_event_snapshot/abc", basic="g.0.eventToken")
    assert data == b"\x89PNG-bytes"
    assert tr.requests[0]["headers"]["Authorization"] == "Basic g.0.eventToken"


def test_nc08b_clip_preview_download_uses_authorization_bearer():
    tr = RecordingTransport([(200, b"mp4-bytes")])
    client = make_client(tr, clock=FakeClock(0.0))
    data = client.download("https://domain/clip/abc", bearer="access-token")
    assert data == b"mp4-bytes"
    assert tr.requests[0]["headers"]["Authorization"] == "Bearer access-token"


def test_nc08c_download_refuses_to_guess_the_scheme():
    client = make_client(RecordingTransport([]), clock=FakeClock(0.0))
    with pytest.raises(ValueError):
        client.download("https://domain/x")
    with pytest.raises(ValueError):
        client.download("https://domain/x", bearer="a", basic="b")


def test_nc08d_download_error_status_becomes_sdm_error():
    tr = RecordingTransport([(504, b"")])
    client = make_client(tr, clock=FakeClock(0.0))
    with pytest.raises(sc.SdmError) as exc:
        client.download("https://domain/x", basic="g.0.eventToken")
    # "Camera image is no longer available for download." → 504 DEADLINE_EXCEEDED
    assert exc.value.rpc_code == "DEADLINE_EXCEEDED"
    assert exc.value.retryable is True


def test_nc08e_download_is_not_limiter_gated():
    """A media host is not an SDM method; the producing call was already counted."""
    limiter = FakeLimiter(allow=False)
    tr = RecordingTransport([(200, b"ok")])
    client = make_client(tr, limiter=limiter, clock=FakeClock(0.0))
    assert client.download("https://domain/x", basic="t") == b"ok"
    assert limiter.acquired == []


# ── NC-09 constants are used, never re-derived ───────────────────────────────


MODULE_PATHS = (
    PKG_ROOT / "iot_asp_autoroute" / "nest" / "auth.py",
    PKG_ROOT / "iot_asp_autoroute" / "nest" / "sdm_client.py",
)


def _executable_string_literals(path: Path) -> list[str]:
    """Every str literal in a module EXCEPT docstrings (which cite sources)."""
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            body = getattr(node, "body", [])
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                docstrings.add(id(body[0].value))
    return [
        n.value
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant)
        and isinstance(n.value, str)
        and id(n) not in docstrings
    ]


def test_nc09_no_hardcoded_endpoints_or_identifiers_in_executable_code():
    """Both modules must read constants.py rather than restate its values.

    Docstrings legitimately quote the endpoints when citing a doc page; running
    code must not, so this walks the AST and skips docstrings.
    """
    frozen_values = {
        nc.SDM_API_BASE,
        nc.SDM_TOKEN_ENDPOINT,
        nc.SDM_OAUTH_SCOPE,
        nc.DEVICE_ACCESS_CONSOLE,
        nc.RATE_LIMIT_RPC_CODE,
        nc.TYPE_CAMERA,
        nc.TRAIT_CONNECTIVITY,
        nc.METHOD_DEVICES_LIST,
    }
    for path in MODULE_PATHS:
        literals = _executable_string_literals(path)
        leaked = sorted(set(literals) & frozen_values)
        assert leaked == [], f"{path.name} restates frozen constants: {leaked}"
        for literal in literals:
            assert "googleapis.com" not in literal, (path.name, literal)
            assert "sdm.devices." not in literal, (path.name, literal)


def test_nc09b_client_status_exposes_the_limiter_snapshot():
    limiter = FakeLimiter()
    client = make_client(RecordingTransport([]), limiter=limiter, clock=FakeClock(5.0))
    state = client.status()
    assert state["daProjectIdSet"] is True
    assert state["calls"] == 0
    assert state["limiter"] == {"now": 5.0, "buckets": {}}


# ── NC-10 no site PII leaves this module on any public path ─────────────────


def test_nc10_module_source_contains_no_real_looking_identifiers():
    """Only Google's documentation placeholders may appear in these files."""
    # Needles are assembled at runtime so this file does not match itself.
    needles = ["home.google" + ".com/home/", "@gmail" + ".com", "@bearresearch" + ".io"]
    for path in (*MODULE_PATHS, Path(__file__)):
        source = path.read_text(encoding="utf-8")
        for needle in needles:
            assert needle not in source, (path.name, needle)
        # Only Google's own placeholders may stand in for a device resource name.
        resource = "enterprises" + "/"
        for line in source.splitlines():
            if resource in line and "resource = " not in line:
                assert "{" in line or PROJECT_ID in line, (path.name, line.strip())


# ── NC-11 interop with the real SdmRateLimiter (when present) ───────────────


def test_nc11_real_limiter_refuses_the_second_call_in_the_same_instant():
    """Contract check against nest.rate_limit, not just the fake.

    Two ``devices.list`` calls at the same clock value must not both go out:
    the second is a local :class:`SdmThrottled` with a future ``retry_at``.
    Skipped (not failed) if that module is not in the tree yet.
    """
    rate_limit = pytest.importorskip("iot_asp_autoroute.nest.rate_limit")

    import random

    limiter = rate_limit.SdmRateLimiter(rng=random.Random(1789))
    tr = RecordingTransport([(200, {"devices": []})])
    clock = FakeClock(0.0)
    client = make_client(tr, limiter=limiter, clock=clock)

    assert client.list_devices() == []
    with pytest.raises(sc.SdmThrottled) as exc:
        client.list_devices()
    assert exc.value.retry_at > clock.t
    assert tr.calls == 1

    # after the documented devices.list floor, the next call is allowed again
    clock.t = exc.value.retry_at
    tr.responses.append((200, {"devices": []}))
    assert client.list_devices() == []
    assert tr.calls == 2


def test_nc10b_client_repr_hides_the_project_id():
    client = make_client(RecordingTransport([]), clock=FakeClock(0.0))
    assert PROJECT_ID not in repr(client)
    assert PROJECT_ID not in str(client.status())
