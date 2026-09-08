import Foundation

/// Node-3 chair LF felt proxy (#18). Not infrasound capture (Safari/BT/phone HPF).
/// Two one-pole stages approximate 0.5–20 Hz energy on |a|.
public struct LfAccelProxyConfig: Equatable, Sendable {
    public var hp: Double
    public var lp: Double
    public var infraThrDb: Double
    public var physicalThrG: Double

    public init(hp: Double = 0.92, lp: Double = 0.15, infraThrDb: Double = -60, physicalThrG: Double = 0.12) {
        self.hp = hp
        self.lp = lp
        self.infraThrDb = infraThrDb
        self.physicalThrG = physicalThrG
    }
}

public final class LfAccelProxy: @unchecked Sendable {
    public var config: LfAccelProxyConfig
    public private(set) var lfEnergyDb: Double = -120
    private var hpState: Double = 0
    private var lpState: Double = 0

    public init(config: LfAccelProxyConfig = LfAccelProxyConfig()) {
        self.config = config
    }

    /// `absA` in g. Returns `infra_felt` when LF proxy is high **and** not a physical thump.
    public func observe(absA: Double) -> String? {
        let hp = absA - hpState
        hpState = config.hp * hpState + (1 - config.hp) * absA
        lpState = (1 - config.lp) * lpState + config.lp * abs(hp)
        let ms = max(lpState * lpState, 1e-12)
        lfEnergyDb = 10 * log10(ms)
        if lfEnergyDb >= config.infraThrDb && absA < config.physicalThrG {
            return "infra_felt"
        }
        return nil
    }

    public static let honesty = "LF accel = felt proxy, not infrasound capture"
}

public enum ChairNodeProfile {
    public static let material: MaterialPreset = .chair
    public static let arming = VibArming.defaults(for: .chair)
    public static let role = "Node 3 — chair-taped structure-borne first; LF TX still lfDriveCapable=false"
}
