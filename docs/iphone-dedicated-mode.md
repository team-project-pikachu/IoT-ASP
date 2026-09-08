# iPhone dedicated mode (checklist)

Public tooling path for phones that stay on the hop / suddenFreq / autoroute fleet. **No site PII.**

## Power (locked)

- Fleet is on **continuous 120 V AC** — see [power-fleet.md](power-fleet.md) / **C5**.
- Keep the phone **plugged in**; treat battery as backup only.

## Google account (Chrome iOS)

Use the **org Google account** for Gemini Enterprise / GCP: active account = `betty@bearresearch.io` (project `bear-iot-asp-rec`). Do not call Gemini from every Safari/Chrome tab — seats live on the hybrid GCP path ([gemini-enterprise.md](gemini-enterprise.md)).

## In-app (web MVP)

1. Add to Home Screen (standalone PWA).
2. Tap **Arm sensors** (or Signal on) once: Web Audio → mic → DeviceMotion → DeviceOrientation ([sensors-chrome-ios.md](sensors-chrome-ios.md)).
3. Pair **1:1** native Bluetooth A2DP to the Soundcore; route via Control Center ([iphone-bluetooth.md](iphone-bluetooth.md)).
4. Default **out = 100%** Web Audio; raise phone + speaker absolute volume separately if SPL must climb (**C4**).
5. Leave **Hold / Manual** off unless a human wants to freeze Gemini patches (**Hold wins** over remote `/patch.json`).
6. Optional LF **10–20 Hz** band: only after capability gate / user arm ([algorithms.md](algorithms.md)).

## OS / device checklist (maximize CPU / RAM availability)

| Setting | Target |
|---------|--------|
| Low Power Mode | **Off** |
| Background App Refresh | On for Safari/Chrome if available |
| Auto-Lock | Longer / never while attended; keep screen awake during armed runs when practical |
| Focus / Do Not Disturb | Prefer not interrupting the tab |
| Close unused heavy apps | Free RAM before long runs |
| Software update mid-run | Avoid |

Native SensorKit / fuller session control remains **#9** ([native-xcode.md](native-xcode.md)).

## Related

- [sdd-app-control.md](sdd-app-control.md) — app as SDD surface
- [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md)
