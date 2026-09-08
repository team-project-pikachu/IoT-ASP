import Foundation

/// Near-ultrasonic mic **contract** for hop 17–23 kHz (#141).
/// Capture I/O lives in `UltrasonicMicCapture` (iOS-only). This type is CLT-safe.
public enum UltrasonicMicMeter {
    public static let preferredSampleRate: Double = 48_000
    public static let hopBandHz: (Double, Double) = (17_000, 23_000)
    public static let micDiffAlpha: Double = 0.85
    public static let fftSize: Int = 2048
    public static let monoChannels: Int = 1

    /// Web `getUserMedia` names — native maps these to `.measurement` (not voice-processing I/O).
    public static let preferEchoCancellationOff = true
    public static let preferNoiseSuppressionOff = true
    public static let preferAutoGainControlOff = true

    public static func nyquist(sampleRate: Double) -> Double { sampleRate / 2.0 }

    public static func usBandFullyNyquist(sampleRate: Double) -> Bool {
        nyquist(sampleRate: sampleRate) + 1e-9 >= hopBandHz.1
    }

    public static func binWidthHz(sampleRate: Double, fftSize: Int = fftSize) -> Double {
        guard fftSize > 0 else { return 0 }
        return sampleRate / Double(fftSize)
    }

    /// Mean dB of bins whose center frequency is inside [17 kHz, 23 kHz].
    /// Empty / no overlap → `-120` (same floor as the web analyser default).
    public static func bandEnergyUs(spectrumDb: [Double], sampleRate: Double, fftSize: Int = fftSize) -> Double {
        let bw = binWidthHz(sampleRate: sampleRate, fftSize: fftSize)
        guard bw > 0, !spectrumDb.isEmpty else { return -120 }
        var sum = 0.0
        var n = 0
        for (i, db) in spectrumDb.enumerated() {
            let f = Double(i) * bw
            if f >= hopBandHz.0 && f <= hopBandHz.1 && db.isFinite {
                sum += db
                n += 1
            }
        }
        return n == 0 ? -120 : sum / Double(n)
    }

    public static func micDiff(micEnergyDb: Double, outLevelDb: Double, alpha: Double = micDiffAlpha) -> Double {
        let a = alpha.isFinite ? alpha : micDiffAlpha
        let mic = micEnergyDb.isFinite ? micEnergyDb : 0
        let out = outLevelDb.isFinite ? outLevelDb : 0
        return (mic - a * out).rounded(toDecimals: 3)
    }
}

private extension Double {
    func rounded(toDecimals n: Int) -> Double {
        let p = pow(10.0, Double(n))
        return (self * p).rounded() / p
    }
}

/// Systems-check snapshot: preferred vs granted rate, AEC/NS/AGC policy vs OS.
public struct UltrasonicMicStatus: Equatable, Sendable {
    public var preferredSampleRate: Double
    public var grantedSampleRate: Double
    public var usBandOk: Bool
    public var aecOffRequested: Bool
    public var nsOffRequested: Bool
    public var agcOffRequested: Bool
    public var osMayOverride: Bool
    public var engineRunning: Bool
    public var lastBandEnergyUs: Double
    public var lastMicDiff: Double?
    public var note: String

    public init(
        preferredSampleRate: Double = UltrasonicMicMeter.preferredSampleRate,
        grantedSampleRate: Double = 0,
        usBandOk: Bool = false,
        aecOffRequested: Bool = true,
        nsOffRequested: Bool = true,
        agcOffRequested: Bool = true,
        osMayOverride: Bool = true,
        engineRunning: Bool = false,
        lastBandEnergyUs: Double = -120,
        lastMicDiff: Double? = nil,
        note: String = "stub / simulator — no device mic"
    ) {
        self.preferredSampleRate = preferredSampleRate
        self.grantedSampleRate = grantedSampleRate
        self.usBandOk = usBandOk
        self.aecOffRequested = aecOffRequested
        self.nsOffRequested = nsOffRequested
        self.agcOffRequested = agcOffRequested
        self.osMayOverride = osMayOverride
        self.engineRunning = engineRunning
        self.lastBandEnergyUs = lastBandEnergyUs
        self.lastMicDiff = lastMicDiff
        self.note = note
    }

    public static func stub(grantedSampleRate: Double = 0) -> UltrasonicMicStatus {
        UltrasonicMicStatus(
            grantedSampleRate: grantedSampleRate,
            usBandOk: UltrasonicMicMeter.usBandFullyNyquist(sampleRate: grantedSampleRate),
            note: grantedSampleRate <= 0
                ? "stub / simulator — no device mic"
                : "granted \(Int(grantedSampleRate)) Hz; Nyquist \(Int(UltrasonicMicMeter.nyquist(sampleRate: grantedSampleRate))) Hz"
        )
    }
}
