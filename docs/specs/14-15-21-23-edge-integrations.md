# #14 / #15 / #21 / #23 — Edge integrations: Pi 5 USB-C node, Apple Home / HomeKit / Matter, Google Home Wi-Fi autorotate, AI Edge Portal

Issues: https://github.com/team-project-pikachu/IoT-ASP/issues/14 · https://github.com/team-project-pikachu/IoT-ASP/issues/15 · https://github.com/team-project-pikachu/IoT-ASP/issues/21 · https://github.com/team-project-pikachu/IoT-ASP/issues/23 · Milestone: M7 — Edge companions (Pi 5 / Apple Home) · Labels: `parked`, `research` / `docs`
Related: `docs/DESIGN_CONSTRAINTS.md` (C1, C2), [18-node3-chair-infrasound.md](18-node3-chair-infrasound.md), [25-hw-limited-lf-aec-micdiff.md](25-hw-limited-lf-aec-micdiff.md), #9 (native SensorKit shell)

## Status

**Parked — research / tracking only.** All four issues say "no implementation this pass". This spec
turns them into one bounded edge roadmap with the invariants that every path must respect: **C1** (phone →
speaker is iOS native A2DP only; no edge path replaces it) and **C2** (the Pi node is USB-C and not in the
web MVP). Vendor facts below were looked up on 2026-09-08 and are cited in *Sources*; nothing here is
built.

## Goal

| Issue | Edge path | What it would add | What it must not do |
|-------|-----------|-------------------|---------------------|
| #14 | **Raspberry Pi 5** field node (USB-C power / data / optional USB audio) | posts the same compact telemetry as phones to the same ingest; optional local sensors (mic / accel / GPIO) for structure-borne / LF proxy; pulls autoroute patches like a phone node | no Pi image, no Matter bridge, no agent swarm (issue non-goals) |
| #15 | **Apple Home / HomeKit or Matter** | presence / accessory-class sensors / room context without a SensorKit entitlement; possible bridge via the Pi | no accessory implementation, no Matter commissioning; **not** a TX path |
| #21 | **Google Home** on **Wi-Fi now**, cellular later | a hardware-limited autorotate control surface (room/structure context, automations) that can flag `suddenFreq` / patch intent to the backend | never replaces iOS A2DP TX (C1); Apple Home stays #15 |
| #23 | **Google AI Edge Portal** | optional packaging: benchmark an on-device LiteRT classifier (vib / burst) across Android devices before shipping it to a Pi/Android companion | not required for the hybrid ADK/Gemini MVP |

## Shipped on `main`

Verified by reading the files (`origin/main` @ `0625e91`):

| What | Where |
|------|-------|
| C2: "Future Raspberry Pi 5 field node uses USB-C for power / data / optional USB audio interface … Not in the public web blaster. Phones remain A2DP TX. Tracking #14" | `docs/DESIGN_CONSTRAINTS.md:15-21` |
| C1: carrier TX is iOS system A2DP; Web Bluetooth / BLE GATT / device pickers forbidden; fuller BT only via a native shell (#9) | `docs/DESIGN_CONSTRAINTS.md:5-13` |
| Edge section: "Raspberry Pi 5 + USB-C (#14) · Apple Home / HomeKit / Matter (#15) — not A2DP TX · SensorKit native shell (#9) · Multi-LLM autoroute registry" | `docs/awesome-iot-asp.md:47-52` |
| Native shell table: `AVAudioSession`, HFP only if elected, CoreBluetooth for **sensors only**, SensorKit parked | `docs/iphone-bluetooth.md:30-37` |
| Ingest surface any node can POST to (`ingest_main.py` → `meta/telemetry/<deviceId>/<ts>.json`); patch object any node can poll | `docs/api-contract.md:23-29`; `services/autoroute-adk/ingest_main.py` |
| Telemetry is device-id keyed and PII-scrubbed server-side (`fleet_log.scrub_pii`, `enrich_telemetry`) — a Pi node needs no new contract | `docs/api-contract.md:94-97`; `fleet_log.py:183-229` (branch) |
| `lfDriveCapable` / `lfArmed` exist precisely so a non-web node can declare LF capability | `docs/api-contract.md:83`; `priors.lf_drive_capable` (`priors.py:203-216`) |
| **No** `net` tag on the wire or in `public/index.html` on `origin/main` (`grep -n "net=\|navigator.connection\|effectiveType" public/index.html` → nothing). Issue #21's "public app already tags net=wifi\|cellular" refers to the owner's Mac clone | — |
| `docs/connectivity-wifi.md` on `origin/main` (#31) | Google Home Wi-Fi-now / cellular-later research answer |
| `docs/ai-edge-portal.md` on `origin/main` (#32) | packaging checklist landed; LiteRT model still optional / not required for MVP |

## Remaining scope

### #14 — Pi 5 USB-C node (when scheduled)

1. **Power / connector (vendor facts):** Pi 5 is powered over **USB-C**; it boots from a 5 V / 3 A (15 W)
   supply but then limits downstream USB to **600 mA**; with a USB-PD supply advertising the optional
   **5 V / 5 A** PDO it allows **1.6 A** to USB peripherals. Official 27 W supply: 5.1 V / 5.0 A (25.5 W).
   `usb_max_current_enable=1` or EEPROM `PSU_MAX_CURRENT=5000` bypass negotiation for non-PD 5 A supplies;
   USB boot is disabled without 5 A. **Design rule:** a USB audio interface + USB mic on the node require
   the 5 A PDO — specify the official 27 W (or 45 W) PSU in the BOM.
2. **Software shape:** a small Python service (stdlib + `requests`/`urllib`) that (a) reads an I²S/USB mic
   and an I²C accelerometer, (b) reuses `iot_asp_autoroute.vib_anomaly` / `features_live` locally for
   `vibClass` / `lfEnergy`, (c) POSTs the `schemaVersion: 1` heartbeat (`deviceId: "pi-<n>"`, `power:
   "ac120"`, `lfDriveCapable` **only** if a real LF-capable output is attached), (d) polls
   `meta/patches/pi-<n>.json`. No new wire fields.
3. **TX (optional):** if the Pi drives a speaker over USB audio it is a *fourth* node with its own
   `deviceId`; it never proxies for a phone (C1 is about phones).
4. Runs in `services/pi-node/` with its own `requirements.txt`; CI import-smokes it without hardware.

### #15 — Apple Home / HomeKit / Matter (research answer)

- Apple's Home app supports these **Matter** accessory types today: air conditioners, bridges, lights,
  locks, outlets, switches, thermostats, blinds/shades, and **sensors (motion, ambient light, contact,
  temperature, humidity)**. There is **no audio/speaker Matter category** in Home, so Matter can never be
  a carrier path (consistent with C1). AirPlay speakers are a separate, non-Matter class and are
  **not** evaluated here (C1 fixes A2DP).
- Usable value: **occupancy / contact / temperature** context for the autoroute (e.g. a `roomOccupied`
  boolean) delivered via HomeKit automations → a webhook → `ingest_main.py` as a telemetry-like event
  under a dedicated `deviceId: "home-bridge"`. Requires an iOS shortcut/automation or a Pi-hosted bridge
  (#14) — never the Safari page.
- Non-goal restated: no accessory implementation, no commissioning.

### #21 — Google Home on Wi-Fi (research answer)

- **Home APIs** (Android + iOS): entities are **Structures → Rooms → Devices** (traits/attributes/commands/
  events) plus **Automations**; access is granted via **OAuth 2.0**; devices may be Matter-backed or
  Cloud-to-cloud. The **Local Home SDK** adds a local Wi-Fi path (discovery via mDNS / UDP / UPnP).
- Design: a Home-APIs automation ("motion in Room B at night") calls a Cloud Run endpoint that writes a
  `suddenFreq`-style event (`event: "home_trigger"`, `deviceId: "home-<room>"`, no room *names* — use
  `node1|node2|node3` mapping kept in `study/`) so the ADK agent can author a clamped patch. The phones
  keep polling; nothing changes on the A2DP path.
- **`net` tag honesty:** the Network Information API (`navigator.connection`, `effectiveType`, `type`) is
  **not supported on Safari / iOS** (MDN BCD). A `net` field emitted by the Mac-clone app is therefore a
  constant `wifi` on iPhones — document it as "assumed", and do not gate behaviour on it. "Cellular later"
  is a backend/agent concern (ingest reachable over the internet), not a phone feature.
- Wire: if `net` is ever added it is an optional string `wifi | cellular | unknown` → integration request
  against `docs/api-contract.md`.

### #23 — AI Edge Portal (research answer)

- Google AI Edge Portal is Google Cloud's service (**private preview**, sign-up form) for benchmarking
  **LiteRT** models across 100+ Android device types on **CPU / GPU / NPU** (NPU: AOT or JIT compilation;
  30+ Qualcomm devices), with models uploaded via UI or from a **GCS bucket**, and dashboards for
  init time, inference latency, memory; LLM benchmarking was added later.
- Relevance: **none for the web fleet** (Safari, no on-device model). It becomes relevant only if a
  LiteRT vib/burst classifier is packaged for an Android or Pi companion (#14). Then: export the SciPy
  heuristic's decision boundary to a tiny LiteRT model, upload from `IOT_ASP_GCS_BUCKET`, benchmark, and
  record `.vv/edge/ai-edge-portal.md`. Optional; not on any milestone path.

## Wire fields

No new required fields. Optional / proposed (each needs an `api-contract.md` integration request before use):

| Field | Type | Owner | Notes |
|-------|------|-------|-------|
| `net` | `wifi \| cellular \| unknown` | #21 | assumed `wifi` on iOS (API unsupported) |
| `event: "home_trigger"` | string value of existing `event` | #15/#21 | reuses the documented `event` alias slot |
| `deviceId: "pi-<n>" \| "home-<node>"` | existing ★ | #14/#15/#21 | ids only; no room names |
| `lfDriveCapable: true` | existing | #14 | only when real LF hardware is attached |

## Clamps / safety

- **C1 / C2 are absolute:** no edge path touches the phone's audio route; the Pi is USB-C and separate.
- Every edge node is just another `deviceId`: the same `validate_patch`, Hold / Manual refusal, band and
  duty clamps apply; a Pi declaring `lfDriveCapable` gets the LF band only through `band_for_telemetry`.
- Home triggers are **inputs** to the agent, never direct patch writers (`meta/patches/` is written only by
  `tools.write_patch`).
- No PII: room / structure identifiers from Home APIs or HomeKit are mapped to `node<N>` outside git;
  OAuth client ids / tokens are secrets **by name** (`IOT_ASP_HOME_OAUTH_CLIENT`, `NOTION_TOKEN`-style);
  never in `public/`.
- Power: continuous 120 V AC fleet (`power: "ac120"`); a Pi on a 3 A brick must not carry a USB audio
  interface (600 mA budget).

## Acceptance tests

Per path, when unparked:

1. #14: `services/pi-node` import smoke without hardware; a fixture heartbeat passes
   `fleet_log.enrich_telemetry` and `is_sudden_freq_event`; a `lfDriveCapable: true` Pi heartbeat with
   `vibClass: infra_felt` yields a `band: "10-20"` patch **only** when `holdManual` is false.
2. #15/#21: a `home_trigger` event with a room name in any key is scrubbed by `scrub_pii` (assert the key is
   dropped and listed in the scrub report); `deviceId` pattern `^(node|pi|home)-?[a-z0-9]+$`.
3. #21: `tests/test_public_html.py` asserts `navigator.connection` is **not** read for control flow (grep
   the file for `effectiveType` → absent) as long as the fleet is iOS-only.
4. #23: none until a LiteRT model exists; then a `.vv/edge/ai-edge-portal.md` evidence file with job id and
   exit code.

## CI gate

- `static_gates` (C1 grep for Web Bluetooth stays), `tests`, `autoroute` dry-run. A future `pi_node` job
  runs the import smoke and fixture tests; no hardware, no network.

## Risks / HW limits

- Pi 5 without a 5 A PDO throttles USB to 600 mA — a USB audio interface + mic will brown out; the
  official 27 W PSU is the safe BOM item.
- Matter has no speaker/audio category in Apple Home; anyone expecting Matter to "route audio" will be
  disappointed by design.
- Google Home APIs need a Developer Console project, OAuth consent, and (for production) certification —
  a heavyweight path for a three-phone fleet; the automation → webhook route is the cheap experiment.
- The Network Information API gap on iOS means `net` can never be trusted from Safari.
- AI Edge Portal is Android-only and in private preview; iPhones are out of scope.

## Sources

- GitHub issues #14, #15, #21, #23 (read via the GitHub connector, 2026-09-08).
- Firecrawl search → Raspberry Pi documentation, "Raspberry Pi computer hardware — Power supply"
  (https://www.raspberrypi.com/documentation/computers/raspberry-pi.html): USB-C on Pi 5; 5.1 V; 3 A boots
  but limits USB to 600 mA; 5 A supply → 1.6 A to USB; 27 W recommended. Raspberry Pi 27W USB-C Power Supply
  page (https://www.raspberrypi.com/products/27w-power-supply/): 5.1 V / 5.0 A, 25.5 W. Raspberry Pi white
  paper "USB Power Delivery on Raspberry Pi 5" (RP-009856-WP-1): only 5 V PDOs requested; optional 5 V 5 A
  PDO; `PSU_MAX_CURRENT`, `usb_max_current_enable=1`; USB boot disabled without 5 A.
- Firecrawl search → Apple Support "Pair and manage your Matter accessories" (https://support.apple.com/en-us/102135):
  supported Matter types list (air conditioners, bridges, lights, locks, outlets, switches, thermostats,
  blinds/shades, sensors: motion, ambient light, contact, temperature, humidity).
- Firecrawl search → Google Home Developers "Home APIs for Android overview"
  (https://developers.home.google.com/apis/android/overview): Structures / Rooms / Devices / Automations;
  Matter-backed or Cloud-to-cloud; OAuth 2.0; Kotlin/Flow. Local Home SDK
  (https://developers.home.google.com/local-home; Google Developers Blog "Local Home SDK ready for Actions"):
  local device discovery over Wi-Fi via mDNS, UDP, UPnP.
- Firecrawl developer search → MDN `NetworkInformation.effectiveType`, `Navigator.connection` browser
  compatibility: Safari and Safari on iOS "No support".
- Firecrawl search → Google for Developers "AI Edge Portal" (https://developers.google.com/edge/ai-edge-portal):
  LiteRT benchmarking across devices, CPU/GPU/NPU (AOT/JIT), upload via UI or GCS bucket, private preview;
  Google Cloud Blog posts (2025-05-20 announcement; later LLM benchmarking).
- Repo: `docs/DESIGN_CONSTRAINTS.md`, `docs/awesome-iot-asp.md`, `docs/iphone-bluetooth.md`,
  `docs/api-contract.md`, `services/autoroute-adk/ingest_main.py`, `priors.py`, `fleet_log.py`.


## Balanced PR4 deepen (research only — no implementation)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Pi 5 (#14) power | USB-C only | C2; not in web MVP |
| Pi telemetry | Same `meta/telemetry/<node>/` contract | No new wire schema |
| HomeKit / Matter (#15) | Presence/context only | Never a TX path (C1) |
| Node 3 chair (#18) | Parked physical mount | `infra_felt` priors already exist; chair not deployed |
| Claim live edge | **Forbidden** this stack | Owner lab required |

Next physical checks (owner): order Pi image research; HomeKit accessory class list; chair tape mount photo + `materialPreset` proposal — still ADR-only until elected.
