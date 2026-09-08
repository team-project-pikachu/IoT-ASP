# #41 — Native iOS and watchOS apps

## Status

Unsigned buildable scaffold; device signing and hardware validation remain pending.

## Goal

Provide native iOS control and a companion watchOS surface while preserving the A2DP-only C1 carrier path.

## Prior art

Reuse shared alarm, sensor, and fleet types under `native/IoTASP/Shared/`; the web PWA remains the deployed MVP.

## Shipped on `main`

No native app is shipped on `main`.

## Remaining scope

Configure signing, validate Watch delivery, and test iPhone/Watch connectivity on owned devices.

## Wire fields

The native alarm mirrors `alarmState`, `impulse`, `volBlast`, `holdManual`, and `vol` from `docs/api-contract.md`.

## Clamps / safety

Hold / Manual clears blast state. Soundcore carrier output uses native iOS A2DP; AirPlay is not C1-compliant.

## Acceptance tests

`swift test` discovers the shared XCTest target, the watch target uses the watch-app product type, and the iOS target embeds Watch content.

## CI gate

Run `cd native/IoTASP && swift test` plus `plutil -lint` for project and plist syntax.

## Risks / HW limits

Full `xcodebuild`, signing, SensorKit entitlement, and device delivery require Xcode and owner hardware.

## Sources

- `docs/native-xcode.md`
- https://developer.apple.com/documentation/watchconnectivity
