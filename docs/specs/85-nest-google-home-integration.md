# #85 — Google Nest Device Access: continuous observation → reactive sound-burst alarm

Issue: https://github.com/team-project-pikachu/IoT-ASP/issues/85 (milestone **M8 — Nest cameras +
Gemini sound-burst MVP**). Siblings: #84 camera discovery/traits · #86 audio/event path · #87 Gemini
Enterprise detector · #88 reactive alarm escalation · #92 gcloud bootstrap · #93 OAuth consent ·
#94 camera device type · #96 event class · #101 PWA surface · #103 CameraSound → detector → alarm ·
#3 continuous polling.

Owned files: `services/autoroute-adk/iot_asp_autoroute/nest/**`, `tests/test_nest_*.py`,
`tests/fixtures/nest/*.json`, `scripts/nest_gcp_bootstrap.sh`, `scripts/nest_dev.sh`,
`scripts/nest_secrets_headless.sh`, `docs/nest-device-access.md`, `docs/accounts-and-seats.md`,
`.cursor/rules/secrets-headless-op.mdc`, `.vv/nest/`, this spec.

## Status

**Implemented.** Merged as PR #107 (squash) plus PR #108, which restores the poller/reactive slice
that auto-merge squashed away at an earlier head. Suite **522 passed**; `ci_static_gates.sh`,
`nest_dev.sh`, `autoroute_dev.sh` and `mdc_convert.py --check` all green.

**Not done and deliberately so:** no live GCP mutation. The agent container has no `gcloud`, no `op`
and no GCP credential, and #85 states agents must not browser-login — so `bear-iot-asp-rec` is
configured by a script the owner runs, not by this branch. Nothing here claims the cloud project is
wired.

## Goal

Let the Nest cameras and doorbells act as a **second acoustic witness** alongside the phones' own
microphones, so an external sound burst reaches a louder alarm through the existing patch path — and
do it **continuously**, without ever bursting against the SDM API.

## Prior art

Checked 2026-09-08 (UTC) in the order CLAUDE.md prescribes; row added to `docs/PRIOR_ART.md`.

- **This repo:** `sudden_freq.author_sudden_freq_patch` already branches on `soundBurst`;
  `mic_diff.burst_decision` already owns the 6 dB micDiff threshold; `features_live.assert_not_patch_path`
  already guards writes. **Reused all three** — `nest/reactive.py:110` delegates rather than
  re-deciding, so there is one authoring implementation and one clamp path.
- **OSS SDM clients** (`google-nest-sdm` as used by Home Assistant, `google-api-python-client`
  discovery access): all cover OAuth + `devices.list/get` + Pub/Sub, none provides a **documented-quota-aware
  paced continuous poller**, which is the one semantic #85 actually needs, and all pull in dependency
  trees the repo's stdlib-first policy excludes. **Built**, and said why here.
- **Transport:** unary `:pull` over `urllib` rather than StreamingPull — StreamingPub is gRPC-only and
  would drag in `google-cloud-pubsub` + `grpcio`. Deliberate dependency-policy choice.

## Shipped on `main`

| What | Where |
|------|-------|
| Frozen identifier/quota contract; cadences **derived**, never hand-tuned | `nest/constants.py:203` (`min_interval_s`), `:259`, `:260` |
| Dual-window sliding limiter + pacing floor | `nest/rate_limit.py:95` (`QuotaBucket`), `:125` |
| OAuth refresh with redacted credentials | `nest/auth.py` |
| SDM client that raises `SdmThrottled` rather than sleeping or bursting | `nest/sdm_client.py:289` |
| Tolerant event parsing, thread de-dup, Pub/Sub pull/ack | `nest/events.py` |
| SDM event → additive `schemaVersion: 1` telemetry, PII-stripped | `nest/mapping.py:162` |
| Continuous scheduler; one API call per step | `nest/poller.py:279`; guard at `:204` |
| Gemini Enterprise burst classifier + offline fallback | `nest/detector.py`; Hold gate at `:210` |
| Nest burst → clamped reactive patch | `nest/reactive.py:110` |
| GCP bootstrap (dry-run default), headless 1Password, offline dry-run | `scripts/nest_gcp_bootstrap.sh`, `scripts/nest_secrets_headless.sh`, `scripts/nest_dev.sh` |

## Remaining scope

- **#101 PWA Nest surface** — read-only status line (last event class, connectivity, event age).
- **Tier-2 audio.** SDM exposes no audio to a backend: `CameraSound.Sound` is a bare detection signal
  and audio exists only on the live stream as Opus. Raw-Opus multimodal needs a WebRTC/RTSP media
  client, which breaks stdlib-first. Seam exists (`AcousticEvidence.audio_ref`); parked with reason.
- **Live GCP apply + `.vv/` read-back** of the `sdm-publisher` binding — owner-run.

## Wire fields (additive; `schemaVersion` stays `1`)

Telemetry: `nestSource`, `nestEvent` (`motion|person|sound|chime|clip_preview`), `nestDeviceType`,
`nestDeviceRef`, `nestEventSessionId`, `nestEventThreadId`, `nestEventThreadState`,
`nestConnectivity`, `nestClipAvailable`, `nestBurstClass`, `nestBurstConfidence`, `nestBurstSource`,
`nestBurstCorroborated`. Acoustic events additionally set the **existing** `soundBurst`, `event` and
`vibClass` so the current burst path reacts with no new semantics.

Patch: `alarmState`, `volBlast`, `trigger` (`nest_sound_burst` | `nest_glass_shatter`) plus the
`nestBurst*` provenance keys.

## Clamps / safety

1. **Hold / Manual wins, three times over** — `detector.escalation_hint` returns `{}`,
   `reactive.author_nest_burst_patch` refuses, and `tools.write_patch` refuses again.
2. **Clamps re-validated after escalation.** An escalated value outside policy is **refused**, never
   silently rewritten (CLAUDE.md invariant 5).
3. **The poller never writes `meta/patches/`.** `poller.assert_telemetry_only` refuses any patch or
   control key on the wire; `FORBIDDEN_KEYS` is pinned by NP-21 against a static-analysis false
   positive that would otherwise have deleted the guard.
4. **Two witnesses to shout.** `volBlast` requires a Nest acoustic event **and** a phone-side onset.
   A false positive drives a physical alarm louder in a residential setting.
5. **PII.** `previewUrl`, raw device ids and structure ids never reach the wire; `nestDeviceRef` is a
   truncated SHA-256. Verified by sentinel tests and a CI gate over tracked files.

## Acceptance tests

`tests/test_nest_rate_limit.py` (624) · `test_nest_sdm.py` (998) · `test_nest_events.py` (729) ·
`test_nest_poller.py` (954) · `test_nest_reactive.py` (225). The quota property is checked **three
independent ways**: the analytic floors from the published numbers, a simulated ≥2 h fleet run, and an
independent sliding-window recomputation from the emitted call log that never reads the limiter's own
state.

## CI gate

`ci_static_gates.sh` adds three gates, each **negative-controlled** (planted input observed to fail,
then removed and green restored): interactive-only 1Password auth; site-identifying Nest resource
names or Google Home structure URLs in tracked files; drift in the documented quota constants.
`ci.yml` asserts the exact `root_agent` tool list, now including `nest_fleet_status` and
`nest_classify_burst`.

## Risks / HW limits

| Risk | Position |
|------|----------|
| SDM is functionally frozen; newer Nest hardware appears only in the mobile-only Home APIs | SDM is the only headless REST + Pub/Sub path; adapter seam kept behind event ingest |
| Quotas are the **sandbox** table; a launched project may differ | Constants gate fails loudly on drift rather than pacing wrong silently |
| `DEVICE_QUOTAS[TYPE_DISPLAY]` is **not documented** — the limits page tabulates only THERMOSTAT, CAMERA and DOORBELL, and says an unlisted type has no instance limit | Kept as a conservative extrapolation from CAMERA and labelled UNVERIFIED in `constants.py`; over-pacing costs freshness, never `RESOURCE_EXHAUSTED` |
| `group:sdm-publisher@googlegroups.com` mis-entered as `serviceAccount:` | Fails **silently** with zero events; bootstrap reads the IAM policy back as evidence |
| Refresh token revoked after 6 months idle | Poller performs the required first `devices.list` on startup |
| Latency floor | Vendor delivery (~1–3 s) + the phone's 2–5 s patch poll dominate; not ours to shorten |

## Sources

<https://developers.google.com/nest/device-access/api> ·
[/project/limits](https://developers.google.com/nest/device-access/project/limits) ·
[/api/events](https://developers.google.com/nest/device-access/api/events) ·
[/subscribe-to-events](https://developers.google.com/nest/device-access/subscribe-to-events) ·
[/authorize](https://developers.google.com/nest/device-access/authorize) ·
[/traits](https://developers.google.com/nest/device-access/traits) ·
[camera-sound](https://developers.google.com/nest/device-access/traits/device/camera-sound) ·
[camera-clip-preview](https://developers.google.com/nest/device-access/traits/device/camera-clip-preview) ·
[camera-live-stream](https://developers.google.com/nest/device-access/traits/device/camera-live-stream) ·
[Pub/Sub pull](https://docs.cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions/pull) ·
[Colab IAM](https://docs.cloud.google.com/colab/docs/access-control) ·
[1Password service accounts](https://www.1password.dev/service-accounts/use-with-1password-cli/) ·
Context7 `/websites/cloud_google_java_reference_google-cloud-discoveryengine`.
