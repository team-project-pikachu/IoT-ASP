# Knowledge Ingest: IoT-ASP vibration / acoustic materials

## Summary
Extracted **7** articles across Apple SensorKit/Core Motion, MDN DeviceMotion, and Anker Soundcore 2 product materials.
Goal: ground parked physical-vs-acoustic vibration response channels for the ultrasonic hop fleet.
Limitations: Apple docs pages are often JS-shell heavy; content quality varies. SensorKit is **native-only** (not available in Safari). Frequency-response curves for Soundcore 2 are not published by Anker.

## Output
- Catalog JSON: `reference/knowledge/catalog.json`
- Per-article markdown under `reference/knowledge/{section}/`
- This report: `reference/knowledge/INGEST.md`

## Sections
- **apple-sensorkit**: 1 article(s)
  - SensorKit | Apple Developer Documentation — `https://developer.apple.com/documentation/sensorkit`
- **apple-coremotion**: 2 article(s)
  - Core Motion | Apple Developer Documentation — `https://developer.apple.com/documentation/coremotion`
  - CMDeviceMotion | Apple Developer Documentation — `https://developer.apple.com/documentation/coremotion/cmdevicemotion`
- **mdn-devicemotion**: 3 article(s)
  - DeviceMotionEvent - Web APIs | MDN — `https://developer.mozilla.org/en-US/docs/Web/API/DeviceMotionEvent`
  - DeviceMotionEvent: acceleration property - Web APIs | MDN — `https://developer.mozilla.org/en-US/docs/Web/API/DeviceMotionEvent/acceleration`
  - DeviceMotionEvent: requestPermission() static method - Web APIs | MDN — `https://developer.mozilla.org/en-US/docs/Web/API/DeviceMotionEvent/requestPermission_static`
- **acoustics-materials**: 1 article(s)
  - Soundcore 2 | Portable Bluetooth Speaker — `https://www.anker.com/ca/products/soundcore-2`

## Failed Or Restricted Pages
- None recorded at scrape layer (empty shells may still lack deep API pages).

## Sources
- https://developer.apple.com/documentation/sensorkit
- https://developer.apple.com/documentation/coremotion
- https://developer.apple.com/documentation/coremotion/cmdevicemotion
- https://developer.mozilla.org/en-US/docs/Web/API/DeviceMotionEvent
- https://developer.mozilla.org/en-US/docs/Web/API/DeviceMotionEvent/acceleration
- https://developer.mozilla.org/en-US/docs/Web/API/DeviceMotionEvent/requestPermission_static
- https://www.anker.com/ca/products/soundcore-2

## Policy notes (physical vs acoustic)
- **Physical vibration** → DeviceMotion / Core Motion linear acceleration (phone body, mount materials).
- **Acoustic vibration** → mic / spectrum energy in-band (air path, speaker cone / Soundcore materials, room surfaces).
- **Material-dependent channel selection** → arm accelerometer vs mic based on setup (phone-on-table vs BT speaker radiate vs over-air listen).
- SensorKit requires a native iOS entitlement; web fleet uses DeviceMotion + Web Audio instead.

## Rerun Inputs
```
workflow: firecrawl-knowledge-ingest
url: https://developer.apple.com/documentation/sensorkit
format: json/markdown/merged
max_pages: 20
also: coremotion, MDN DeviceMotionEvent (+ acceleration, requestPermission), anker soundcore-2
```