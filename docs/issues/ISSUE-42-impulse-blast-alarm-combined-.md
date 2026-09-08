# ISSUE-42 — Impulse→blast + alarm reactivity (web + native)

**Issue:** https://github.com/team-project-pikachu/IoT-ASP/issues/42  
**Status:** stubbed → working web slice (PR2)

## Did

- Web alarm state machine + Simulate impulse button
- Telemetry: impulse / volBlast / alarmState
- Native mirror remains in `native/IoTASP/` (stack PR4 deepen)

## Didn't

- Claim signed App Store / live HW
- SensorKit entitlement

## Next

- DeviceMotion permission UX on Safari; native CoreMotion already on main via #40
