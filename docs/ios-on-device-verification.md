# On-device verification — sensors + ultrasonic (#151)

CI stub (`make native-check` / `IoTASPSmoke`) **cannot** prove this. Humans run these on a signed device. No invented SensorKit approvals.

## Checklist

- [ ] Permission sequencing (mic, then motion) — #144
- [ ] Systems check: 48 kHz preference vs granted, AEC/NS/AGC off requested, motionOk, route/sink — #141 #146
- [ ] CoreMotion + impulse; ultrasonic band energy with a known tone — #140 #4 #5
- [ ] Soundcore A2DP vs built-in; Sonos route if hardware present — #146
- [ ] Telemetry schemaVersion 1 POST + patch poll (mock URL OK) — #147
- [ ] Backgrounding pauses sensing honestly — #145
- [ ] SensorKit no-op unless #148 checklist is complete

Fill `docs/ios-device-capability-matrix.md` cells only after this run. Record evidence under `.vv/151/` (no secrets, no site PII).
