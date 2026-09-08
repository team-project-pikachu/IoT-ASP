import Foundation

/// Honest availability for non-CoreMotion phone sensors (#142).
/// Ambient light is **not** a public continuous third-party API on modern iOS.
public enum OtherSensorKind: String, CaseIterable, Sendable {
    case ambientLight
    case barometerAltimeter
    case proximity
    case cameraAsLightProxy
}

public struct OtherSensorRow: Equatable, Sendable {
    public var kind: OtherSensorKind
    public var publicAPI: String
    public var entitlement: Bool
    public var mvpUse: String
    public var available: Bool
    public var statusCopy: String
}

public enum OtherSensorsGate {
    public static func table(altimeterHardware: Bool) -> [OtherSensorRow] {
        [
            OtherSensorRow(
                kind: .ambientLight,
                publicAPI: "none (no public lux stream)",
                entitlement: false,
                mvpUse: "n/a — do not emit fake lux",
                available: false,
                statusCopy: "Ambient light: unavailable to third-party apps"
            ),
            OtherSensorRow(
                kind: .barometerAltimeter,
                publicAPI: "CMAltimeter.isRelativeAltitudeAvailable",
                entitlement: false,
                mvpUse: "optional relative altitude only",
                available: altimeterHardware,
                statusCopy: altimeterHardware ? "Altimeter: hardware present" : "Altimeter: not available"
            ),
            OtherSensorRow(
                kind: .proximity,
                publicAPI: "UIDevice.isProximityMonitoringEnabled (display-driven)",
                entitlement: false,
                mvpUse: "out of scope for hop",
                available: false,
                statusCopy: "Proximity: out of scope"
            ),
            OtherSensorRow(
                kind: .cameraAsLightProxy,
                publicAPI: "AVCaptureDevice (privacy-heavy)",
                entitlement: false,
                mvpUse: "default out",
                available: false,
                statusCopy: "Camera-as-lux: not used"
            ),
        ]
    }

    /// Never invent a lux number.
    public static func ambientLux() -> Double? { nil }
}
