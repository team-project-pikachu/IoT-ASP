import Foundation

#if canImport(SensorKit)
import SensorKit
#endif

/// SensorKit is entitlement-gated. Do not invent approval.
/// Entitlement: com.apple.developer.sensorkit.reader.allow
/// Docs: https://developer.apple.com/documentation/sensorkit
public enum SensorKitGate {
    public static var isLinked: Bool {
        #if canImport(SensorKit)
        true
        #else
        false
        #endif
    }

    public static var entitlementDeclared: Bool {
        // Info only — real entitlement must be granted by Apple for a research study.
        false
    }

    public static func startReadersIfEntitled() {
        #if canImport(SensorKit) && ASP_SENSORKIT_ENTITLED
        // Stub: SRSensorReader for accelerometer / rotationRate when approved.
        // See docs/sensorkit-watch.md
        #else
        // No-op: CoreMotion path is primary for fleet phones.
        #endif
    }
}
