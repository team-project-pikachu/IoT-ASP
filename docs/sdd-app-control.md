# Software-defined driving via the app

Public scientific tooling: the **browser app is the SDD control surface** for the acoustic plant (near-ultrasonic hop / suddenFreq / Gemini autoroute). Humans and Gemini drive parameters through the UI and patch loop — not speaker hardware knobs alone.

## Loop (discover → model → plan → execute)

| Phase | Who | What |
|-------|-----|------|
| **Discover** | Phone sensors + Systems check / **Arm sensors** | Mic (raw), DeviceMotion / orientation, Web Audio unlock; optional Ambient Light if present |
| **Model** | Local vib class + suddenFreq heuristics; GCP ADK/Gemini when online | Map telemetry → algo / band / dwell / gain proposal |
| **Plan** | `patch.json` (mock or worker) | Clamped param patch (`schemaVersion: 1`); rationale in monitor |
| **Execute** | Web Audio → **iPhone native Bluetooth A2DP** → paired speaker | Apply patch unless **Hold / Manual**; carrier out at max practical in-app gain by default |

## Hot-apply (engine) vs page reload (HTML)

- **Engine updates** (backend / Gemini autoroute / timestore / dry or live `patch.json`) are **hot-applied** by the continuous poll (`POLL_MS`, default **3 s**, clamp 2–5 s). The open tab updates algo / volume / bands without F5 or pull-to-refresh.
- **HTML deploys** (new `public/index.html` on Vercel) still need **one** browser load after publish — that is shell code, not the param engine.
- See [api-contract.md](api-contract.md) for poll / cache-bust details.

## Control surface (non-negotiable)

1. **App owns software gain and algorithm** — slider / autoroute set Web Audio level and mode.
2. **OS owns the BT sink** — pair 1:1 in Settings; route via Control Center ([iphone-bluetooth.md](iphone-bluetooth.md)).
3. **Hold / Manual** freezes remote patches so the human keeps the knobs; does not disable local Signal / sensors.
4. **No site PII** on the public deploy.

## Loudness warning

Default and clamp ceiling target **maximum practical Web Audio gain** (UI 100%). **Bluetooth absolute volume** and **speaker hardware / DSP** still limit real SPL. Raise phone + Soundcore volume separately if the plant must be louder.

## Related

- [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) — C1 native BT, C3 SDD, C4 max gain path
- [sensors-chrome-ios.md](sensors-chrome-ios.md) — Chrome iOS arm sequence
- [autoroute.md](autoroute.md) — suddenFreq → Gemini
- Shared SDD rules: `~/kb/rules/shared-rules.md` / workspace `00-shared`
