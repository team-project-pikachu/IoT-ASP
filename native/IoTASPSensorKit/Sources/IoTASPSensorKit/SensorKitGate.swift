import Foundation

#if canImport(SensorKit)
import SensorKit
#endif

/// SensorKit is entitlement-gated. Do **not** invent Apple approval or secrets.
///
/// Entitlement key (when Apple grants a research study):
/// `com.apple.developer.sensorkit.reader.allow`
/// Docs: https://developer.apple.com/documentation/sensorkit
///
/// Compile modes:
/// - **Stub (default / CI):** no `-DASP_SENSORKIT_ENTITLED` → readers are no-ops.
/// - **Entitled (device + owner grant):** build with `-DASP_SENSORKIT_ENTITLED` **and**
///   uncomment keys in `Resources/SensorKit.entitlements.example` after real approval.
public enum SensorKitGate {
    /// True when the SensorKit framework is linkable on this SDK.
    public static var isLinked: Bool {
        #if canImport(SensorKit)
        true
        #else
        false
        #endif
    }

    /// True only when this binary was compiled with the entitled flag.
    /// Runtime entitlement presence is still an Apple / provisioning question —
    /// this flag never invents a grant.
    public static var entitlementDeclared: Bool {
        #if ASP_SENSORKIT_ENTITLED
        true
        #else
        false
        #endif
    }

    /// Human-readable mode for UI / Systems-check rows.
    public static var modeLabel: String {
        if entitlementDeclared && isLinked { return "entitled" }
        if isLinked { return "linked-stub" }
        return "stub"
    }

    /// Start SensorKit readers when entitled; otherwise no-op (CoreMotion / mic stay primary).
    public static func startReadersIfEntitled() {
        #if canImport(SensorKit) && ASP_SENSORKIT_ENTITLED
        // Owner-approved path only: wire SRSensorReader for accelerometer / rotationRate.
        // Symbols: SRAccelerometerSensor, SRRotationRateSensor — see docs/sensorkit-watch.md
        _ = SensorKitReaderStub.entitledPlaceholder
        #else
        // Stub: fleet phones use CoreMotion (`native/IoTASPMotionAudio` / PhoneMotionLogger).
        #endif
    }

    /// Sample stream hook for product surfaces (HomeNestAlarm / Glass Shatter / hop).
    /// Always returns stub samples unless entitled readers are live.
    public static func latestStubSample() -> SensorKitSample {
        SensorKitSample.stubUnavailable()
    }
}

/// Placeholder type kept behind the entitled compile gate so CI never needs SensorKit symbols.
enum SensorKitReaderStub {
    static let entitledPlaceholder = true
}

/// Minimal vib-oriented sample shared with hop / Nest acoustic stubs (no SensorKit types).
public struct SensorKitSample: Sendable, Equatable {
    public var ax: Double
    public var ay: Double
    public var az: Double
    public var gx: Double
    public var gy: Double
    public var gz: Double
    public var source: String
    public var entitled: Bool
    public var ts: Date

    public init(
        ax: Double = 0,
        ay: Double = 0,
        az: Double = 0,
        gx: Double = 0,
        gy: Double = 0,
        gz: Double = 0,
        source: String,
        entitled: Bool,
        ts: Date = Date()
    ) {
        self.ax = ax
        self.ay = ay
        self.az = az
        self.gx = gx
        self.gy = gy
        self.gz = gz
        self.source = source
        self.entitled = entitled
        self.ts = ts
    }

    public static func stubUnavailable(ts: Date = Date()) -> SensorKitSample {
        SensorKitSample(
            source: "sensorkit_stub",
            entitled: false,
            ts: ts
        )
    }

    public var absA: Double {
        (ax * ax + ay * ay + az * az).squareRoot()
    }
}
