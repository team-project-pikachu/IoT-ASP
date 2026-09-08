# Google Nest Device Access — owner setup (console steps)

**Scope:** how the IoT-ASP fleet observes Google Nest cameras/doorbells through the **Smart Device
Management (SDM) API**, and the console steps only the account owner can perform.

**Agents do not browser-login** (issue [#85](https://github.com/team-project-pikachu/IoT-ASP/issues/85)).
Everything below is either a documented owner step or a deterministic script the owner runs. No agent
in this repo authenticates interactively, and no credential value is ever committed.

Related: [`docs/specs/85-nest-google-home-integration.md`](specs/85-nest-google-home-integration.md) ·
[`docs/api-contract.md`](api-contract.md) · [`scripts/nest_gcp_bootstrap.sh`](../scripts/nest_gcp_bootstrap.sh)

---

## 0. Two different "projects" — do not conflate them

| Name | Where | Looks like | Used for |
|------|-------|-----------|----------|
| **Device Access project id** | https://console.nest.google.com/device-access | UUID, e.g. `32c4c2bc-fe0d-461b-b51c-f3885afff2f0` | the `enterprises/<project-id>/…` path in every SDM call, and the PCM consent URL |
| **Google Cloud project id** | https://console.cloud.google.com | `bear-iot-asp-rec` | enabling APIs, hosting the Pub/Sub topic, Secret Manager, the poller service account |

The SDM `enterprises/…` path takes the **Device Access** id, never `bear-iot-asp-rec`. Getting this
wrong produces a confusing `PERMISSION_DENIED` rather than a "wrong project" error.

Source: <https://developers.google.com/nest/device-access/get-started>

---

## 1. Device Access Console registration (owner, one time)

1. Open <https://console.nest.google.com/device-access>.
2. Accept the Device Access Terms of Service and pay the **one-time, non-refundable US$5 fee per
   account**.
3. Create a project. Note the **Project ID (UUID)** it returns.
4. Paste the OAuth **Client ID** from step 2 below.
5. Choose **Enable events**, then supply the **Pub/Sub Topic ID** created in step 3.

> **Account type matters.** Device Access requires a **consumer Google Account**; Google Workspace
> accounts are not supported. This is the one documented exception to the repo's preference for the
> org account in public docs, so this file names no address at all — the owner account is referenced
> only by the secret name `NEST_DA_OWNER_ACCOUNT` in 1Password Environment `dev`. The same account
> must own the Nest devices in the Google Home app, and must be the account that completes the
> consent flow in step 4.

Sandbox account caps (not rate limits): **3 projects**, **25 users**, **5 structures**, **5 users per
structure**.

Sources: <https://developers.google.com/nest/device-access/get-started> ·
<https://developers.google.com/nest/device-access/project/limits>

---

## 2. Google Cloud OAuth client (owner, one time)

1. In <https://console.cloud.google.com> select project **`bear-iot-asp-rec`**.
2. Enable the Smart Device Management API:
   <https://console.developers.google.com/apis/library/smartdevicemanagement.googleapis.com>
3. Create an **OAuth 2.0 Client ID** (Web application) at
   <https://console.developers.google.com/apis/credentials> with authorized redirect URI
   **`https://www.google.com`**.
4. An OAuth Client ID must be valid and unique to one Device Access project and cannot be shared
   across projects.

Store the client id and secret under the names in §6 — never in this repo.

Source: <https://developers.google.com/nest/device-access/get-started>

---

## 3. Google Cloud plumbing (scripted)

Run the repo's bootstrap rather than clicking. It is idempotent and **defaults to `--dry-run`**, so it
prints its plan and mutates nothing until you pass `--apply`:

```bash
bash scripts/nest_gcp_bootstrap.sh                 # dry run: print the exact plan (no credentials needed)
bash scripts/nest_gcp_bootstrap.sh --apply         # owner runs this once, authenticated as the project owner
```

It enables `smartdevicemanagement.googleapis.com`, `pubsub.googleapis.com` and
`secretmanager.googleapis.com`; creates the self-hosted Pub/Sub topic and pull subscription; grants the
Google-managed SDM publisher principal permission to publish into that topic; creates the poller
service account with the minimum roles; and creates the **secret names** (never values).

> **Self-hosted topic.** Device Access projects created **after January 2025** must host their own
> Pub/Sub topic in their own Cloud project; older projects were given a Google-hosted
> `projects/sdm-prod/topics/enterprise-<project-id>` topic. `bear-iot-asp-rec` is on the self-hosted
> path. Source: <https://developers.google.com/nest/device-access/api/events>

---

## 4. Authorize the account (owner, browser — once)

Open the Partner Connections Manager URL for the Device Access project, signed in as the account that
owns the Nest devices:

```
https://nestservices.google.com/partnerconnections/<DA-PROJECT-ID>/auth
  ?redirect_uri=https://www.google.com
  &access_type=offline
  &prompt=consent
  &client_id=<OAUTH-CLIENT-ID>
  &response_type=code
  &scope=https://www.googleapis.com/auth/sdm.service
```

Grant the device permissions, then take the `code` from the redirect and exchange it once for a
refresh token:

```bash
curl -sS -X POST https://oauth2.googleapis.com/token \
  -d client_id="$NEST_OAUTH_CLIENT_ID" \
  -d client_secret="$NEST_OAUTH_CLIENT_SECRET" \
  -d code="$AUTH_CODE" \
  -d grant_type=authorization_code \
  -d redirect_uri=https://www.google.com
```

Store the returned `refresh_token` under `NEST_REFRESH_TOKEN` (§6). The access token expires; the
service refreshes it itself.

> **Authorization is not complete until the first `devices.list` call succeeds** with the new token.
> Until then, events are not delivered. The poller performs this call on startup for exactly this
> reason. Source: <https://developers.google.com/nest/device-access/authorize>

---

## 5. Why the fleet **paces** instead of bursting

The SDM API publishes hard quotas, and one of them is hourly — which is what makes naive polling fail
in the field rather than in a unit test:

| Unit | Documented limit | Sustained floor |
|------|------------------|-----------------|
| `devices.list` | 5 QPM | **12.0 s** between calls |
| `devices.get` | 10 QPM | 6.0 s (project-wide) |
| `devices.executeCommand` | 10 QPM | 6.0 s |
| `structures.*` / `rooms.*` | 5 QPM | 12.0 s |
| each trait command | 5 QPM per project, per user, per device | 12.0 s |
| **camera / doorbell instance** | **30 QPM or 100 QPH** | **36.0 s** — the hourly cap binds |
| thermostat instance | 5 QPM or 100 QPH | 36.0 s |

Exceeding a quota returns `RESOURCE_EXHAUSTED` ("Rate limited."). Because `devices.get` is 10 QPM
project-wide and each camera needs ≥36 s spacing, one project sustains **6 cameras** on the polling
path. Beyond that, liveness reconciliation must slow down further.

The design consequence is a **hybrid**: Pub/Sub **events** carry the fast reactive signal (they cost no
SDM quota), and **polling** carries slow liveness/connectivity reconciliation at the floors above.
`iot_asp_autoroute/nest/rate_limit.py` enforces both windows simultaneously, and
`iot_asp_autoroute/nest/poller.py` executes at most one API call per step — a burst is impossible by
construction, not merely discouraged.

Source: <https://developers.google.com/nest/device-access/project/limits>

---

## 6. Secret names (values never in git, chat, issues or CI logs)

| Name | Holds | Home |
|------|-------|------|
| `NEST_DA_PROJECT_ID` | Device Access project UUID | 1Password Environment `dev` → Secret Manager |
| `NEST_OAUTH_CLIENT_ID` | OAuth 2.0 client id | 1Password Environment `dev` → Secret Manager |
| `NEST_OAUTH_CLIENT_SECRET` | OAuth 2.0 client secret | 1Password Environment `dev` → Secret Manager |
| `NEST_REFRESH_TOKEN` | long-lived refresh token from §4 | 1Password Environment `dev` → Secret Manager |
| `NEST_PUBSUB_SUBSCRIPTION` | `projects/bear-iot-asp-rec/subscriptions/<id>` | env / Secret Manager |
| `GOOGLE_CLOUD_PROJECT` | `bear-iot-asp-rec` | env |
| `NEST_DA_OWNER_ACCOUNT` | the consumer Google Account that owns the devices | 1Password Environment `dev` only |

Resolution order in code: process env → Secret Manager → (owner's laptop) 1Password `dev`.
`nest/auth.py` redacts every one of these from `repr`, logs and exception messages, and
`tests/test_nest_sdm.py` asserts a sentinel value never escapes.

---

## 7. Privacy posture

Camera clip preview URLs, still-image URLs, raw SDM device ids and structure ids are **recording URIs
and site identifiers** under CLAUDE.md invariant #7. They may be handled in memory and written to the
**private** `meta/nest/` GCS tree, but they never reach the public repo, the telemetry heartbeat, the
PWA, or `.vv/` evidence. The wire carries `nestDeviceRef` — a truncated SHA-256 of the device id —
instead. `scripts/ci_static_gates.sh` greps tracked files for real-looking ids and Home app URLs.

No audio or video is transcribed, stored publicly, or fed to a model from this repo. What crosses the
wire from a Nest observation is an **event class** (`sound`, `motion`, `person`, `chime`,
`clip_preview`) and a timestamp — not content.

---

## 8. M8 platform matrix

Delivery surfaces × Nest hardware × SDM / ASP event classes (stub vs live gates):  
[`docs/specs/100-platform-matrix.md`](specs/100-platform-matrix.md) (issue [#100](https://github.com/team-project-pikachu/IoT-ASP/issues/100)).
