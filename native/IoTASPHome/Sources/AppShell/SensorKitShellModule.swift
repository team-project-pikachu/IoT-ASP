import Foundation

#if canImport(SensorKit)
import SensorKit
#endif

/// SensorKit-ready shell slot (#109). Does **not** request or invent entitlements.
/// Implementation package: sibling #110 → `native/IoTASPSensorKit` (when merged).
public struct SensorKitShellModule: AppShellModule {
    public let id = "sensorkit"
    public let title = "SensorKit"
    public let systemImage = "sensor.tag.radiowaves.forward"

    public init() {}

    public var frameworkLinked: Bool {
        #if canImport(SensorKit)
        true
        #else
        false
        #endif
    }

    /// Always false in this shell — Apple research entitlement is human-gated (#110 / #113).
    public var entitlementDeclared: Bool { false }

    public var modeLabel: String {
        if entitlementDeclared && frameworkLinked { return "entitled" }
        if frameworkLinked { return "framework-linked (stub / not entitled)" }
        return "stub (SensorKit unavailable on this SDK)"
    }

    public var statusSummary: String {
        "Placeholder tab. Wire readers via #110 IoTASPSensorKit after Apple grant. Entitlement key name only: com.apple.developer.sensorkit.reader.allow — do not uncomment without human approval."
    }
}
