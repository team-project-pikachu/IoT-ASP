import Foundation

/// Concrete SensorKit classes we *could* request (#143).
/// Runtime: if not entitled, log/status and fall back to CoreMotion. Never invent grants.
public enum SensorKitReaderKind: String, CaseIterable, Sendable {
    case accelerometer
    case rotationRate
    case ambientLightSensor
    case deviceUsageReport
    case visits
}

public struct SensorKitReaderSpec: Equatable, Sendable {
    public var kind: SensorKitReaderKind
    public var appleSymbol: String
    public var requestableInCode: Bool
    public var requiresAppleGrant: Bool
    public var fallback: String
}

public enum SensorKitReaderMap {
    public static let entitlement = "com.apple.developer.sensorkit.reader.allow"

    public static let specs: [SensorKitReaderSpec] = [
        SensorKitReaderSpec(kind: .accelerometer, appleSymbol: "SRSensorAccelerometer", requestableInCode: true, requiresAppleGrant: true, fallback: "CoreMotion accelerometer (#140)"),
        SensorKitReaderSpec(kind: .rotationRate, appleSymbol: "SRSensorRotationRate", requestableInCode: true, requiresAppleGrant: true, fallback: "CoreMotion gyro / deviceMotion (#140)"),
        SensorKitReaderSpec(kind: .ambientLightSensor, appleSymbol: "SRSensorAmbientLightSensor", requestableInCode: true, requiresAppleGrant: true, fallback: "unavailable (#142)"),
        SensorKitReaderSpec(kind: .deviceUsageReport, appleSymbol: "SRSensorDeviceUsageReport", requestableInCode: true, requiresAppleGrant: true, fallback: "skip — not hop-vib"),
        SensorKitReaderSpec(kind: .visits, appleSymbol: "SRSensorVisits", requestableInCode: true, requiresAppleGrant: true, fallback: "skip — PII risk"),
    ]

    public static func start(entitled: Bool) -> String {
        if !entitled {
            return "SensorKit skipped (not entitled); CoreMotion is primary"
        }
        return "SensorKit readers would start here after Apple grant + provisioning"
    }

    public static func stop() {}
}
