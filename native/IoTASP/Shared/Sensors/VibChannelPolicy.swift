import Foundation

/// Material-dependent physical vs acoustic arming (#6).
/// Wire name `materialPreset`: handheld | table | chair | speaker.
public enum MaterialPreset: String, CaseIterable, Sendable, Codable {
    case handheld
    case table
    case chair
    case speaker
}

public struct VibArming: Equatable, Sendable {
    public var physical: Bool
    public var acoustic: Bool

    public init(physical: Bool, acoustic: Bool) {
        self.physical = physical
        self.acoustic = acoustic
    }

    public static func defaults(for preset: MaterialPreset) -> VibArming {
        switch preset {
        case .table:
            return VibArming(physical: true, acoustic: false)
        case .speaker:
            return VibArming(physical: true, acoustic: true)
        case .handheld:
            return VibArming(physical: false, acoustic: true)
        case .chair:
            return VibArming(physical: true, acoustic: false)
        }
    }
}

public enum VibChannelPolicy {
    public static func classify(
        physical: PhysicalVibEvent,
        acoustic: AcousticVibEvent,
        arming: VibArming
    ) -> String {
        if arming.physical, physical != .none { return "physical" }
        if arming.acoustic, acoustic == .acousticBurst || acoustic == .acoustic { return "acoustic" }
        return "none"
    }

    public static func unknownPresetFallsBack(_ raw: String) -> MaterialPreset {
        MaterialPreset(rawValue: raw) ?? .handheld
    }
}
