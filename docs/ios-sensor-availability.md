# iOS sensor availability (honest)

Issue #142. Native table: `OtherSensorsGate`.

| Sensor | Public API | Entitlement? | MVP hop / Nest / Glass |
|--------|------------|--------------|------------------------|
| Ambient light | **None** for third-party continuous lux | no | n/a — **no fake lux in telemetry** |
| Barometer / altimeter | `CMAltimeter` when `isRelativeAltitudeAvailable` | no | optional (#140) |
| Proximity | display-driven `UIDevice` | no | out of scope |
| Camera as light | AVCapture (privacy-heavy) | camera usage | **default out** |
| SensorKit ambient / usage | SensorKit | **yes** (`com.apple.developer.sensorkit.reader.allow`) | stub until #148 |

See also device matrix (#149).
