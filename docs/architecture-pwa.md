# Vercel PWA platform architecture (hop-ultrasonic)

**TL;DR:** `public/` is a static blaster: Web Audio + Hold/Manual + patch poll. Backend (GCP/ADK) owns ingest and writes clamped `patch.json`. No Vertex keys in the browser. No service worker that caches patches. This doc does **not** invent Nest OAuth client IDs, SensorKit grants, or browser Vertex keys.

**Status:** living · **Canonical for:** macOS / Mac Studio + web fleet control surface  
**Live:** https://hop-ultrasonic.vercel.app/ · **Source:** `public/` · **Index:** [README.md](README.md)  
**Aligned to:** [PRD.md](PRD.md) · [roadmap.md](roadmap.md) · [api-contract.md](api-contract.md) · [TESTING_PLAN.md](TESTING_PLAN.md) · [deploy.md](deploy.md)

## 1. Role in the product

| Concern | Owns | Does not own |
|---------|------|--------------|
| **Vercel static PWA** | UI + Web Audio TX/RX metering, Hold/Manual, patch poll, optional telemetry beacon, fleet BroadcastChannel | Gemini/Vertex calls, ADK agent runtime, Nest OAuth, SensorKit |
| **GCP / ADK backend** | Ingest → GCS → clamped `patch.json` authorship | Browser shell HTML deploys |
| **Native iOS** | Entitled sensors, A2DP session honesty, on-device UAT | Replacing the PWA as the macOS Studio control surface |

**Pattern (Vercel AI lens):** durable **control surface** + **telemetry/patch** contract — not an in-browser agent. Agentic autoroute runs **off-browser**; the PWA only applies clamped patches and freezes them under Hold/Manual.

## 2. Surfaces

```text
┌─────────────────────────────────────────────────────────────┐
│  Browser (Mac Studio / desktop / iPhone Safari/Chrome)       │
│  public/index.html  ·  manifest.webmanifest  ·  icons        │
│  Web Audio 17–23 kHz · Hold/Manual · systems check           │
└───────────────┬───────────────────────────┬─────────────────┘
                │ GET /patch.json (?patch=) │ POST/beacon (?telemetry=)
                ▼                           ▼
┌───────────────────────────┐   ┌──────────────────────────────┐
│ Static mock on Vercel     │   │ GCP ingest (Cloud Run/CF)    │
│ Cache-Control: no-store   │   │ → GCS meta/telemetry/…       │
└───────────────────────────┘   └──────────────┬───────────────┘
                                               ▼
                                    ADK / Gemini autoroute
                                               │
                                               ▼
                                    clamped patch object (GCS/CDN)
```

| Artifact | Purpose |
|----------|---------|
| `public/index.html` | Single-file blaster (HTML + CSS + one `<script>`) |
| `public/manifest.webmanifest` | PWA install metadata (`display: standalone`) |
| `public/patch.json` | Offline mock patch (`schemaVersion: 1`) |
| `vercel.json` | Headers (Permissions-Policy, patch `no-store`), `cleanUrls`, Git auto-deploy off on `main` |
| `public/README.txt` | Field record (fleet nodes, no PII) |

**Deploy:** GitHub Actions owns ship of `public/` ([deploy.md](deploy.md)); Vercel Git auto-deploy on `main` is disabled (`git.deploymentEnabled.main: false`).

**Service worker:** none. Do not add a SW that network-falls-back-caches `index.html` over `/patch.json` without an explicit network-first rule for patches ([api-contract.md](api-contract.md)).

## 3. Data flows

| Flow | Mechanism | Notes |
|------|-----------|-------|
| **Patch poll** | `GET` `/patch.json` or `?patch=` / `BACKEND_*` | Interval 2–5 s (default 3 s); `cache: "no-store"` + `_cb=` bust; Hold short-circuits apply |
| **Telemetry** | `POST` / `sendBeacon` when URL set | Empty URL = offline; device metrics only; no UA/geo/PII keys |
| **Fleet local** | `BroadcastChannel("iot-asp-fleet")` | Same-origin tabs only; peer cards until native/#10 |
| **Gemini flag** | Telemetry / UI reflection of patch meta | **No** API keys in browser; flag is advisory for humans |

### Hot-apply vs HTML deploy

| Change | Client | Refresh? |
|--------|--------|----------|
| Engine params (`patch.json`) | `applyPatch` in-session | No (≤ one poll) |
| `public/index.html` deploy | New shell | Yes, once after deploy |

## 4. Agentic hooks (browser-safe)

```text
suddenFreq / micDiff / impulse  →  telemetry beacon
                                      │
                                      ▼
                              GCP ingest + ADK
                                      │
                                      ▼
                              clamped patch.json
                                      │
                 ┌────────────────────┴────────────────────┐
                 ▼                                         ▼
          pollPatch / applyPatch              Hold / Manual = freeze
          (vol, band, dwell, algo, seed)      (patches ignored; local
                                               knobs + optional sudden
                                               rotate may continue)
```

**Invariants:** C1 (no Web Bluetooth TX), C4/C6 band clamps (public TX **17–23 kHz** only), HOLD1 (Hold freezes remote apply), SCH1 (`schemaVersion: 1`). Secrets stay in env / 1Password / Actions names only.

## 5. Platform detect & Sonos route

| Detection | Signal | Product use |
|-----------|--------|-------------|
| **iPhone / iOS** | UA + `maxTouchPoints` / iPadDesktopUA | Phone fleet ops; A2DP is OS-native |
| **macOS desktop** | Mac UA without multi-touch desktop-iPad spoof | Studio / desktop blaster |
| **mac-studio** | Optional UA-CH architecture hint | Prefer Studio labeling when available |
| **audioSink** | Default `sonos-beam-2` label | Honesty: Sonos DSP may crush US carriers; Soundcore remains C1 primary |

Sonos Beam Gen 2 is a **system/AirPlay sink** story (milestone **Sonos**), not a Web Bluetooth target. Ultrasonic FR is experimental — systems-check rows must stay honest.

## Deep dive — areas, tests, non-goals

## 6. Map to areas & milestones

| Layer | `area:*` | Milestone | Primary issues |
|-------|----------|-----------|----------------|
| Static PWA shell, Hold, seeds, monitor | `area:agentic` | **macOS / Mac Studio** | #1 (closed), #61/#62 (open) |
| Patch/telemetry contract, autoroute clamps | `area:agentic`, `area:adk` | **Platform / Agentic / ADK** | #12 (closed), #60/#64 (open) |
| Soundcore / mic honesty | `area:drivers` | macOS + iOS | #43 (closed), #141/#146 (open) |
| Nest glass / SDM UI stubs | `area:sdk`, `area:agentic` | **Nest** | #101 (open); no OAuth invent |
| Beam Gen 2 route | `area:drivers` | **Sonos** | #39/#120 (open) |

**Drain order:** Platform contract → macOS PWA field → iOS → Nest → Sonos ([roadmap.md](roadmap.md)).

## 7. Test seams (per layer)

| Layer | Seam | Primary tests |
|-------|------|---------------|
| Static HTML invariants | String / parse gates on `public/index.html` | `tests/test_public_html.py`, `tests/test_pwa_phase_macos.py` |
| Vercel config | `vercel.json` headers / patch no-store / no SW claim | `tests/test_pwa_phase_macos.py` |
| PWA manifest | `manifest.webmanifest` fields | `tests/test_pwa_phase_macos.py` |
| Hold / patch / band | Function-body asserts + Playwright | `test_public_html.py`, `tests/e2e/public_smoke.spec.mjs` |
| Platform detect | `detectPlatform()` body | `test_detect_platform_mac_vs_iphone`, phase macos |
| Fleet / impulse / alarm | BroadcastChannel + simImpulse | unit + e2e fleet test |
| Deploy / webhooks | Workflow + HMAC stubs | `test_deploy_workflow.py`, `test_vercel_webhook*.py` |
| Autoroute backend | Dry-run clamps (not in browser) | `scripts/autoroute_dev.sh`, `test_agent_import.py` |
| Issue ↔ test matrix | Closed-first traceability | [test-traceability.md](test-traceability.md), `tests/fixtures/issue_test_map.json` |

## 8. Non-goals (architect reminder)

- Nest OAuth client IDs or live SDM tokens in fixtures.
- In-browser Vertex/Gemini SDK with embedded keys.
- Claiming ambient-light or LF 10–20 Hz TX on the public ship slice without HW gate + PRD election.
- Service-worker caching that shadows patch hot-apply.

## Related

- Constraints: [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) · ADK: [adk-autoroute.md](adk-autoroute.md) · V&V: [vv/README.md](vv/README.md)
- Traceability: [test-traceability.md](test-traceability.md) · Closed log: [mvp-closed-log.md](mvp-closed-log.md)
