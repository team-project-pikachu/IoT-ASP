# Connectivity — Google Home Wi‑Fi now, cellular later (#21)

**Status:** Docs MVP / research lane. Hardware-limited autorotate control surface.

## Intent

Use **Google Home** on **Wi‑Fi** as the near-term household control path for
hardware-limited autorotate. **Cellular** is explicitly deferred.

This does **not** replace iOS native **A2DP TX** (DESIGN_CONSTRAINTS **C1**).
Apple Home / Matter remains parked research (issue **#15**).

## Planned connectivity tagging

The public app is expected to tag telemetry with
`net=wifi|cellular` when the Network Information API is available (defaulting to
**wifi** if unknown). This is planned behavior; the current telemetry schema
does not include the tag yet. When implemented, the tag will be observational
only — carrier audio still exits via OS Bluetooth A2DP.

## Phasing

| Phase | Path | Notes |
|-------|------|-------|
| Now | Wi‑Fi + Google Home | Control / presence / routine hooks at home LAN |
| Later | Cellular | Fleet / away-from-home; no MVP requirement |
| Parked | Apple Home / Matter | See #15 — do not conflate with Google Home Wi‑Fi |

## Non-goals (this issue)

- No Web Bluetooth TX for carrier audio
- No street-level site PII in connectivity docs or telemetry
- No forced cellular modem bring-up in Vercel static app

## Related

- Issue **#21**
- [autoroute.md](autoroute.md) — suddenFreq → Gemini autorotate loop
- [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) — C1 native A2DP
- [iphone-bluetooth.md](iphone-bluetooth.md) — BT route limits
- Issue **#15** — Apple Home / Matter (parked)
