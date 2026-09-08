# #94 / #95 — research notes (not closing)

## #94 Camera device type integration (Home Device API)

**Stub shipped with #97:** `NestCameraCatalog` / `NestCameraDevice` / `CameraSnapshotContext`
in `native/IoTASPHome/Sources/HomeNestAlarm/CameraDeviceStub.swift`.

**Still blocked / remaining:** live Home Device API trait enumeration from Nest hardware
(requires GoogleHomeSDK + Nest premium OAuth). Leave issue open until live traits land.

## #95 Glass shatter discovery (event-triggered acoustic)

**Heuristic stub already exists** via #96 thresholds (`riseMs` ≤ 80 → `glass_shatter`).

**Parked / blocked research:** real shatter ML / dataset distinct from heuristic.
Skip closing; no additional stub-only slice beyond #96/#97.
