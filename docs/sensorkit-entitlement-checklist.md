# Apple Developer / SensorKit entitlement checklist (#148)

**Agents must not invent OAuth client IDs, Nest tokens, or SensorKit entitlement approvals.**
CLI help only — no Apple Developer portal automation.

Status in this repo: **not approved**. `ASP_SENSORKIT_ENTITLED` stays off. CI stays on the stub path.

## Owner checklist (fill with real evidence later)

- [ ] Apple Developer Program membership / team / bundle ID `io.bearresearch.iotasp` ownership confirmed
- [ ] App ID capability requested: `com.apple.developer.sensorkit.reader.allow`
- [ ] Research / study requirements documented per Apple SensorKit program (human completes portal)
- [ ] Provisioning profile regenerated **after** real approval
- [ ] CI remains on stub path until approval evidence exists
- [ ] Record approved/not-approved in private study notes if needed — **no secrets in public issues**

## Flip condition

Only the owner marks this complete. Then a follow-up PR may define `ASP_SENSORKIT_ENTITLED` for device builds. Until then, CoreMotion is primary (`SensorKitReaderMap.start(entitled: false)`).

## Related

#110 stub, #143 reader map, #113 privacy docs, `native/IoTASP/SYSTEMS-CHECK.md`.
