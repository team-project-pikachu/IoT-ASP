import Foundation

/// Acoustic (air-path) vib channel (#5).
/// Burst = energy − rolling median ≥ 12 dB. Prefer `micDiff` when present so self-TX
/// does not trigger (best-effort; not full AEC — see #25).
public struct AcousticVibConfig: Equatable, Sendable {
    public var burstMarginDb: Double
    public var floorDb: Double
    public var window: Int

    public init(burstMarginDb: Double = 12, floorDb: Double = -55, window: Int = 50) {
        self.burstMarginDb = burstMarginDb
        self.floorDb = floorDb
        self.window = max(3, window)
    }
}

public enum AcousticVibEvent: String, Sendable, Equatable {
    case none
    case acoustic
    case acousticBurst
}

public final class AcousticVibChannel: @unchecked Sendable {
    public var config: AcousticVibConfig
    public private(set) var lastEnergy: Double = -120
    public private(set) var lastMedian: Double = -120
    private var ring: [Double] = []

    public init(config: AcousticVibConfig = AcousticVibConfig()) {
        self.config = config
    }

    public func observe(energyDb: Double, micDiffDb: Double? = nil, armed: Bool = true) -> AcousticVibEvent {
        guard armed else { return .none }
        let metric = micDiffDb ?? energyDb
        lastEnergy = metric
        ring.append(metric)
        if ring.count > config.window { ring.removeFirst(ring.count - config.window) }
        lastMedian = Self.median(ring)
        if metric - lastMedian >= config.burstMarginDb {
            return .acousticBurst
        }
        if metric >= config.floorDb {
            return .acoustic
        }
        return .none
    }

    public static func median(_ xs: [Double]) -> Double {
        guard !xs.isEmpty else { return -120 }
        let s = xs.sorted()
        let m = s.count / 2
        if s.count % 2 == 0 {
            return (s[m - 1] + s[m]) / 2
        }
        return s[m]
    }
}
