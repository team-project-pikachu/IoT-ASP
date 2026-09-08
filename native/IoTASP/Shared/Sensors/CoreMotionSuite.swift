import Foundation

/// Full CoreMotion suite **models** for hop-ultrasonic vib science (#140).
/// Hardware I/O lives in `PhoneMotionLogger` (iOS-only; excluded from SPM on CLT).
/// This module is Foundation-only so `swift build` on Command Line Tools stays green.
public enum CoreMotionSuite {
    /// Align Info.plist / README: 1–100 Hz vib science.
    public static let hzMin: Double = 1
    public static let hzMax: Double = 100
    public static let defaultHz: Double = 50
    /// Standard gravity for m/s² → g (backend `vib_anomaly` is documented in g).
    public static let standardGravity: Double = 9.80665

    public static func clampHz(_ hz: Double) -> Double {
        if hz.isNaN || hz.isInfinite { return defaultHz }
        return min(hzMax, max(hzMin, hz))
    }

    public static func interval(hz: Double) -> TimeInterval {
        1.0 / clampHz(hz)
    }

    public static func metersPerSecondSquaredToG(_ mps2: Double) -> Double {
        mps2 / standardGravity
    }
}

/// Concrete CoreMotion classes we will request. Pedometer is product-skipped.
public enum MotionSensorClass: String, CaseIterable, Sendable, Codable {
    case accelerometer
    case gyroscope
    case magnetometer
    case deviceMotion
    case pedometer
    case altimeter
}

public enum MotionProductUse: String, Sendable, Codable {
    case fleetVib
    case optional
    case skip
}

public enum CoreMotionPolicy {
    public static func productUse(for cls: MotionSensorClass) -> MotionProductUse {
        switch cls {
        case .accelerometer, .gyroscope, .deviceMotion:
            return .fleetVib
        case .magnetometer, .altimeter:
            return .optional
        case .pedometer:
            return .skip
        }
    }

    /// Why a class is skipped or optional. `nil` means primary fleet path.
    public static func skipRationale(for cls: MotionSensorClass) -> String? {
        switch cls {
        case .pedometer:
            return "Pedometer step counts are not a hop-ultrasonic / vib-science input; skip."
        case .altimeter:
            return "Relative altimeter only when CMAltimeter.isRelativeAltitudeAvailable; otherwise skip."
        case .magnetometer:
            return "Magnetometer is optional; indoor calibration/noise makes it a heading hint, not vibClass."
        case .accelerometer, .gyroscope, .deviceMotion:
            return nil
        }
    }

    public static var apiSurface: [(MotionSensorClass, MotionProductUse, String)] {
        MotionSensorClass.allCases.map { cls in
            let use = productUse(for: cls)
            let note: String
            switch cls {
            case .accelerometer:
                note = "CMMotionManager.startAccelerometerUpdates — raw user-frame accel (g)."
            case .gyroscope:
                note = "CMMotionManager.startGyroUpdates — rotationRate rad/s."
            case .magnetometer:
                note = "CMMotionManager.startMagnetometerUpdates — µT; noisy indoors."
            case .deviceMotion:
                note = "CMMotionManager.startDeviceMotionUpdates — attitude/gravity/userAcceleration."
            case .pedometer:
                note = "CMPedometer skipped for hop fleet."
            case .altimeter:
                note = "CMAltimeter relative altitude when hardware reports available."
            }
            return (cls, use, note)
        }
    }
}

/// Simulator-safe availability. All-false is the CLT / Simulator default.
public struct MotionAvailability: Equatable, Sendable {
    public var accelerometer: Bool
    public var gyroscope: Bool
    public var magnetometer: Bool
    public var deviceMotion: Bool
    public var pedometer: Bool
    public var altimeter: Bool

    public init(
        accelerometer: Bool = false,
        gyroscope: Bool = false,
        magnetometer: Bool = false,
        deviceMotion: Bool = false,
        pedometer: Bool = false,
        altimeter: Bool = false
    ) {
        self.accelerometer = accelerometer
        self.gyroscope = gyroscope
        self.magnetometer = magnetometer
        self.deviceMotion = deviceMotion
        self.pedometer = pedometer
        self.altimeter = altimeter
    }

    public static let simulatorSafe = MotionAvailability()

    public func isAvailable(_ cls: MotionSensorClass) -> Bool {
        switch cls {
        case .accelerometer: return accelerometer
        case .gyroscope: return gyroscope
        case .magnetometer: return magnetometer
        case .deviceMotion: return deviceMotion
        case .pedometer: return pedometer
        case .altimeter: return altimeter
        }
    }
}

/// Which streams to arm. Never starts pedometer. Altimeter only if available.
public struct MotionStreamPlan: Equatable, Sendable {
    public var hz: Double
    public var rawAccelerometer: Bool
    public var rawGyroscope: Bool
    public var magnetometer: Bool
    public var deviceMotion: Bool
    public var altimeter: Bool

    public init(
        hz: Double = CoreMotionSuite.defaultHz,
        rawAccelerometer: Bool = false,
        rawGyroscope: Bool = false,
        magnetometer: Bool = false,
        deviceMotion: Bool = false,
        altimeter: Bool = false
    ) {
        self.hz = CoreMotionSuite.clampHz(hz)
        self.rawAccelerometer = rawAccelerometer
        self.rawGyroscope = rawGyroscope
        self.magnetometer = magnetometer
        self.deviceMotion = deviceMotion
        self.altimeter = altimeter
    }

    /// Scientific default: arm every **available** fleet-relevant stream; never pedometer.
    public static func scientific(
        availability: MotionAvailability,
        hz: Double = CoreMotionSuite.defaultHz
    ) -> MotionStreamPlan {
        MotionStreamPlan(
            hz: hz,
            rawAccelerometer: availability.accelerometer,
            rawGyroscope: availability.gyroscope,
            magnetometer: availability.magnetometer,
            deviceMotion: availability.deviceMotion,
            altimeter: availability.altimeter
        )
    }

    public var armsAnything: Bool {
        rawAccelerometer || rawGyroscope || magnetometer || deviceMotion || altimeter
    }
}

/// Fused sample matching `docs/api-contract.md` axes (`ax/ay/az`, `gx/gy/gz`).
public struct FullMotionSample: Sendable, Equatable {
    public var ax: Double
    public var ay: Double
    public var az: Double
    public var gx: Double
    public var gy: Double
    public var gz: Double
    public var mx: Double?
    public var my: Double?
    public var mz: Double?
    public var roll: Double?
    public var pitch: Double?
    public var yaw: Double?
    public var gravityX: Double?
    public var gravityY: Double?
    public var gravityZ: Double?
    public var relativeAltitudeM: Double?
    public var ts: Date

    public var absA: Double { (ax * ax + ay * ay + az * az).squareRoot() }
    public var absOmega: Double { (gx * gx + gy * gy + gz * gz).squareRoot() }

    public init(
        ax: Double = 0,
        ay: Double = 0,
        az: Double = 0,
        gx: Double = 0,
        gy: Double = 0,
        gz: Double = 0,
        mx: Double? = nil,
        my: Double? = nil,
        mz: Double? = nil,
        roll: Double? = nil,
        pitch: Double? = nil,
        yaw: Double? = nil,
        gravityX: Double? = nil,
        gravityY: Double? = nil,
        gravityZ: Double? = nil,
        relativeAltitudeM: Double? = nil,
        ts: Date = Date()
    ) {
        self.ax = ax
        self.ay = ay
        self.az = az
        self.gx = gx
        self.gy = gy
        self.gz = gz
        self.mx = mx
        self.my = my
        self.mz = mz
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        self.gravityX = gravityX
        self.gravityY = gravityY
        self.gravityZ = gravityZ
        self.relativeAltitudeM = relativeAltitudeM
        self.ts = ts
    }

    public func vibSample() -> VibSample {
        VibSample(ax: ax, ay: ay, az: az, gx: gx, gy: gy, gz: gz, ts: ts)
    }

    /// Wire keys from `docs/api-contract.md` — no new schemaVersion.
    public func telemetryAxes() -> [String: Double] {
        var out: [String: Double] = [
            "ax": ax, "ay": ay, "az": az,
            "gx": gx, "gy": gy, "gz": gz,
            "absA": absA, "absOmega": absOmega,
        ]
        if let mx { out["mx"] = mx }
        if let my { out["my"] = my }
        if let mz { out["mz"] = mz }
        return out
    }
}
