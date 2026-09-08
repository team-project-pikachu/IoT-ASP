# Fleet power — continuous 120 V AC

**Formal constraint:** [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) **C5**.  
Public scientific tooling. **No site PII.**

## Invariant

All study/tooling fleet nodes run on **continuous 120 V AC** mains (North America residential):

| Node class | Power assumption |
|------------|------------------|
| iPhone field nodes | Plugged in / always charging (not battery-limited) |
| Soundcore 2 (or equivalent) | AC-capable dock / always charging when used for long runs |
| Future Pi / edge nodes | Mains or USB-C from a 120 V supply (#14) |

## Consequences for control software

1. **Dedicated mode** — Low Power Mode **off** is consistent; no battery duty-cycle ([iphone-dedicated-mode.md](iphone-dedicated-mode.md)).
2. **Night window (22:00–07:00 America/New_York)** — volume 0→100% glides/jumps in **0.5** UI steps are **not** battery-save ramps; they are schedule/courtesy curves only.
3. **Autoroute / Gemini** — do **not** assume brownout, thermal battery throttle, or “save charge” caps when proposing gain/dwell.
4. **Systems check** — report power as `ac120` / continuous when documenting fleet health (no street addresses).

## Related

- [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) C4 (max Web Audio gain) · C5 (this page)
- [iphone-dedicated-mode.md](iphone-dedicated-mode.md)
- [algorithms.md](algorithms.md) night / band notes
