# Privacy / entitlements — native iOS (SensorKit · CoreMotion · mic)

**Issue:** [#113](https://github.com/team-project-pikachu/IoT-ASP/issues/113) · **Milestone:** [M9 — Native iOS app (SensorKit + Swift libs)](https://github.com/team-project-pikachu/IoT-ASP/milestone/10)  
**Tone:** MVP · constraint-aligned with M8/M9 (no invented credentials or entitlement grants)

This is the **docs drain** for privacy strings, entitlement names, and what **humans** must approve in Apple Developer / SensorKit programs. It does **not** grant SensorKit access, ship a signed App Store build, or authorize Nest/Home OAuth.

---

## M5 research vs M9 build (do not conflate)

| Milestone | Scope | Privacy / entitlement reality |
|-----------|--------|-------------------------------|
| **M5** (#9) | Research closeout only | Web **cannot** SensorKit; entitlement path **parked**; evidence in [`.vv/9/`](../.vv/9/) |
| **M9** (#109–#113) | Buildable native shell + libs + CI + **this docs lane** | CoreMotion + mic usage strings ship with the app sketch; SensorKit entitlement remains **commented / stub** until Apple research approval |

Canonical M5 freeze: [sensorkit-research-closeout.md](sensorkit-research-closeout.md).  
Native build matrix / honesty table: [native-xcode.md](native-xcode.md).  
Private study protocol (site PII): [STUDY_PRIVATE.md](STUDY_PRIVATE.md) — never commit street addresses or recording URIs to public `main`.

---

## Info.plist usage strings (required for shipping surfaces)

Keys must be present before the OS will allow the corresponding API. Missing keys → crash / hard deny at first access (Apple Core Motion guidance).

### Present in-repo today (`native/IoTASP/`)

| Target | Key | Purpose | Current string (summary) |
|--------|-----|---------|--------------------------|
| **IoTASPApp** | `NSMotionUsageDescription` | CoreMotion accel / gyro 1–100 Hz vib logging | Vibration science; intense 10–20 Hz band |
| **IoTASPApp** | `NSMicrophoneUsageDescription` | AVFoundation / micDiff impulse (not SensorKit) | Mic for micDiff impulse detection |
| **IoTASPWatch** | `NSMotionUsageDescription` | On-wrist impulse / vib for alarm reactivity | Watch vib logging |

Paths: `native/IoTASP/IoTASPApp/Info.plist`, `native/IoTASP/IoTASPWatch/Info.plist`.

### SensorKit (not active — human + Apple gate)

When (and only when) a research study is approved and entitlement strings are uncommented, follow Apple’s setup guide:

- [Configuring your project for sensor reading](https://developer.apple.com/documentation/sensorkit/configuring-your-project-for-sensor-reading)
- Entitlement doc: [`com.apple.developer.sensorkit.reader.allow`](https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.sensorkit.reader.allow)

**Agents must not invent** SensorKit Info.plist privacy prose or claim keys are “live” while the entitlement remains commented. Add SensorKit usage metadata in the same PR that flips the entitlement **after** human confirmation of Apple approval.

Local ingest (research): `reference/knowledge/apple-sensorkit/`, `reference/knowledge/apple-coremotion/`.

---

## Entitlement names (SensorKit)

| Entitlement key | Type | Status in repo |
|-----------------|------|----------------|
| `com.apple.developer.sensorkit.reader.allow` | Array of sensor identifiers | **Commented out** in `native/IoTASP/IoTASPApp/IoTASP.entitlements` |

Example sensor identifier strings (from public Spezi / Apple SensorKit naming — **not** enabled here):

| Sensor (product intent) | Typical entitlement array value |
|-------------------------|----------------------------------|
| Accelerometer | `motion-accelerometer` |
| Rotation / related motion streams | per Apple / study design (see SensorKit `SRSensor` list) |
| Ambient light | `ambient-light-sensor` |
| On-wrist (Watch pairing context) | `on-wrist` |
| Pedometer | `pedometer` |

Gate in code: `#if canImport(SensorKit) && ASP_SENSORKIT_ENTITLED` → `Shared/Sensors/SensorKitGate.swift`.  
`SensorKitGate.entitlementDeclared` is intentionally **`false`** until a human uncomments the entitlement and Apple has granted the capability for a **preapproved research study**.

**CoreMotion and microphone do not use the SensorKit entitlement.** They use the Info.plist usage descriptions above + standard user prompts.

---

## Human approvals (checklist)

| Gate | Who | Agent may |
|------|-----|-----------|
| SensorKit research-study entitlement in Apple Developer | Human owner | Document names/links only; leave keys commented |
| App Store / TestFlight signing & provisioning | Human | Point at Xcode workflow in [native-xcode.md](native-xcode.md); no fake profiles in git |
| Nest / Google Home OAuth client IDs & tokens | Human (M8) | Stub / env **references** only — see M8 milestone constraints |
| Privacy string copy changes | Human review on PR | Draft strings; do not invent “approved by Apple” claims |
| Ambient capture / study upload of mic audio | Human + private study package | Public docs: no site PII ([STUDY_PRIVATE.md](STUDY_PRIVATE.md)) |

---

## Agent constraints (hard)

Aligned with M8/M9 milestone descriptions and #113 acceptance:

1. **Do not invent** OAuth client IDs, Nest tokens, SensorKit entitlement grants, provisioning profiles, or App Store credentials.
2. **Do not** uncomment `com.apple.developer.sensorkit.reader.allow` or set `ASP_SENSORKIT_ENTITLED` without an explicit human “Apple approved” note on the issue/PR.
3. **Do not** claim Web / PWA can use SensorKit — M5 closed that research ([sensorkit-research-closeout.md](sensorkit-research-closeout.md)).
4. Prefer **CLI help only** for cloud/auth tooling (see runbook). No browser OAuth flows; no ad-hoc HTTPS consoles to mint secrets.
5. No street addresses, neighbor identifiers, or recording URIs in public docs / `.vv/` / CI logs.

---

## Agent runbook (gh / git / gcloud CLI help only)

Short path for agents working M9 privacy/docs or native stubs:

```bash
# Issue + milestone context
gh issue view 113 --repo team-project-pikachu/IoT-ASP
gh api repos/team-project-pikachu/IoT-ASP/milestones/10 --jq '{title,description,state}'

# Branch from main (docs-only for #113)
git fetch origin main
git switch -c m9/113-privacy-entitlements-docs origin/main

# Inspect what is actually in-tree (do not invent)
git grep -n 'NSMotionUsageDescription\|NSMicrophoneUsageDescription\|sensorkit.reader' -- native/IoTASP docs

# GCP help text only if needed for env var *names* (never paste secrets)
gcloud --help
gcloud auth application-default print-access-token --help   # help only; do not mint Nest tokens

# PR
git push -u origin HEAD
gh pr create --repo team-project-pikachu/IoT-ASP --title 'docs(m9): privacy/entitlements for SensorKit + motion + mic' --body 'Closes #113'
```

Related code PRs (#109–#112) own app shell / SensorKit stub / CoreMotion+AVFoundation / CI — **this issue stays docs**. Do not fight those trees for `native/` or `Makefile` churn.

---

## Related

- [native-xcode.md](native-xcode.md) — build matrix + entitlement honesty  
- [sensorkit-watch.md](sensorkit-watch.md) — vib bands + Watch companion  
- [iphone-bluetooth.md](iphone-bluetooth.md) — `AVAudioSession` / A2DP (C1)  
- [algorithms.md](algorithms.md) § Privacy — ambient capture may include speech  
- [awesome-iot-asp.md](awesome-iot-asp.md) — index  
- Apple: [SensorKit](https://developer.apple.com/documentation/sensorkit) · [Core Motion](https://developer.apple.com/documentation/coremotion) · [AVFoundation](https://developer.apple.com/documentation/avfoundation)
