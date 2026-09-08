# iOS background / continuous sensing (#145)

Fleet phones are on **120 V AC** (`docs/api-contract.md`) — that does **not** override iOS background limits.

## MVP

Foreground: CoreMotion + mic capture (primary).

On lock / background / phone call / route change: **pause sensing** (`BackgroundSensingPolicy.onEnterBackground` → `backgroundPaused`). Do not fake always-on mic.

## Background modes

| Mode | Elected? | Why |
|------|----------|-----|
| `audio` | only if hop TX is audibly playing | Silent keep-alive is App Review risk and a lie |
| `bluetooth-central` | **no** | C1 is system A2DP, not CoreBluetooth |
| `location` | **no** | not vib science |
| `processing` | **no** | not a sensor entitlement |

## Scientific run

Keep app foreground. Guided Access / dedicated mode: `docs/iphone-dedicated-mode.md`.
