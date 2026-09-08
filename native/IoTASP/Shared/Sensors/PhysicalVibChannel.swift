import Foundation

/// Physical (structure-borne) vib channel (#4).
/// Prefers gravity-excluded accel in **g**. Debounced class + shake → hop / reseed.
public struct PhysicalVibConfig: Equatable, Sendable {
    public var thresholdG: Double
    public var debounceMs: Double
    public var shakeMultiple: Double
    public var shakeWindowMs: Double
    public var reseedEvery: Int

    public init(
        thresholdG: Double = 0.12,
        debounceMs: Double = 300,
        shakeMultiple: Double = 3,
        shakeWindowMs: Double = 400,
        reseedEvery: Int = 4
    ) {
        self.thresholdG = min(2.0, max(0.01, thresholdG))
        self.debounceMs = debounceMs
        self.shakeMultiple = shakeMultiple
        self.shakeWindowMs = shakeWindowMs
        self.reseedEvery = max(1, reseedEvery)
    }
}

public enum PhysicalVibEvent: String, Sendable, Equatable {
    case none
    case physical
    case shakeHop
    case shakeReseed
}

public final class PhysicalVibChannel: @unchecked Sendable {
    public var config: PhysicalVibConfig
    public private(set) var shakeCount: Int = 0
    public private(set) var lastClass: String = "none"
    private var lastEmit: Date?
    private var lastShakeCandidate: Date?

    public init(config: PhysicalVibConfig = PhysicalVibConfig()) {
        self.config = config
    }

    /// `absA` must already be in **g** (use `CoreMotionSuite.metersPerSecondSquaredToG` if needed).
    public func observe(absA: Double, now: Date = Date(), armed: Bool = true) -> PhysicalVibEvent {
        guard armed else {
            lastClass = "none"
            return .none
        }
        let thr = config.thresholdG
        let shakeThr = thr * config.shakeMultiple
        if absA >= shakeThr {
            if let prev = lastShakeCandidate, now.timeIntervalSince(prev) * 1000 <= config.shakeWindowMs {
                lastShakeCandidate = nil
                if debounceOK(now) {
                    shakeCount += 1
                    lastEmit = now
                    lastClass = "physical"
                    return shakeCount % config.reseedEvery == 0 ? .shakeReseed : .shakeHop
                }
            } else {
                lastShakeCandidate = now
                return .none
            }
        }
        if absA >= thr, debounceOK(now) {
            lastEmit = now
            lastClass = "physical"
            return .physical
        }
        if absA < thr * 0.4 {
            lastClass = "none"
        }
        return .none
    }

    private func debounceOK(_ now: Date) -> Bool {
        guard let last = lastEmit else { return true }
        return now.timeIntervalSince(last) * 1000 >= config.debounceMs
    }
}
