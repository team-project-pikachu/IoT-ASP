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

    public static func startReadersIfEntitled() -> String {
        #if canImport(SensorKit) && ASP_SENSORKIT_ENTITLED
        return SensorKitReaderMap.start(entitled: true)
        #else
        return SensorKitReaderMap.start(entitled: false)
        #endif
    }
}
