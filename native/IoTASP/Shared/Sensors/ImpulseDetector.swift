import Foundation

/// 1–100 Hz vib logging priority; 10–20 Hz = intense vib band (align infra_felt / LF gate).
public enum VibBand: String, Sendable {
    case broadband_1_100 = "1-100"
    case intense_10_20 = "10-20"
}

public struct VibSample: Sendable {
    public var ax: Double
    public var ay: Double
    public var az: Double
    public var gx: Double
    public var gy: Double
    public var gz: Double
    public var absA: Double
    public var absOmega: Double
    public var ts: Date

    public init(ax: Double, ay: Double, az: Double, gx: Double, gy: Double, gz: Double, ts: Date = Date()) {
        self.ax = ax
        self.ay = ay
        self.az = az
        self.gx = gx
        self.gy = gy
        self.gz = gz
        self.absA = (ax * ax + ay * ay + az * az).squareRoot()
        self.absOmega = (gx * gx + gy * gy + gz * gz).squareRoot()
        self.ts = ts
    }
}

public final class ImpulseDetector: @unchecked Sendable {
    /// Accel spike threshold (g-ish user units from CoreMotion userAcceleration).
    public var accelOnset: Double = 0.45
    /// micDiff onset (dB above baseline) — mirror web BURST_ONSET_DB ~9.
    public var micDiffOnsetDb: Double = 9
    /// Max rise time to count as impulse (ms).
    public var maxRiseMs: Double = 120

    private var accelBaseline: Double = 0.05
    private var micBaseline: Double = -80

    public init() {}

    public func observeAccel(_ sample: VibSample) -> ImpulseEvent? {
        let ema = 0.9 * accelBaseline + 0.1 * sample.absA
        let delta = sample.absA - accelBaseline
        accelBaseline = ema
        guard delta >= accelOnset else { return nil }
        return ImpulseEvent(fromAccel: true, fromMicDiff: false, riseMs: maxRiseMs / 2)
    }

    public func observeMicDiff(_ micDiffDb: Double) -> ImpulseEvent? {
        let ema = 0.9 * micBaseline + 0.1 * micDiffDb
        let delta = micDiffDb - micBaseline
        micBaseline = ema
        guard delta >= micDiffOnsetDb else { return nil }
        return ImpulseEvent(fromAccel: false, fromMicDiff: true, riseMs: maxRiseMs / 2)
    }

    /// Intense vib flag when LF accel energy concentrates in ~10–20 Hz proxy (native sample rate dependent).
    public func intenseVibProxy(absA: Double, lfEnergyProxy: Double) -> Bool {
        lfEnergyProxy > 0.08 && absA > 0.12
    }
}
