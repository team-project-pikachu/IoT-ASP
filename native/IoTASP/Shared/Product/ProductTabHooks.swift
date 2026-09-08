import Foundation

/// Native product-tab mapping for Nest / Glass Shatter (#150).
/// Nest OAuth is parked — no live tokens.
public enum ProductTab: String, CaseIterable, Sendable {
    case hop
    case homeNestAlarm
    case glassShatter
}

public enum ProductEventClass: String, Sendable {
    case none
    case sound_burst
    case glass_shatter
}

public enum ProductTabHooks {
    public static let nestOAuthParked = true

    public static func classify(acoustic: AcousticVibEvent, impulse: ImpulseEvent?) -> ProductEventClass {
        if acoustic == .acousticBurst { return .sound_burst }
        if let e = impulse, e.fromMicDiff { return .sound_burst }
        if acoustic == .acoustic { return .sound_burst }
        return .none
    }

    /// Glass shatter is a sibling story — native demo uses the same burst path without claiming a classifier.
    public static func tab(for event: ProductEventClass) -> ProductTab {
        switch event {
        case .glass_shatter: return .glassShatter
        case .sound_burst: return .homeNestAlarm
        case .none: return .hop
        }
    }

    public static func demoWithoutNestTokens(alarm: AlarmStateMachine, event: ProductEventClass, now: Date = Date()) {
        guard event != .none else { return }
        if alarm.holdManual { return }
        alarm.tick(now: now, impulseEvent: ImpulseEvent(fromAccel: false, fromMicDiff: true, riseMs: 40), nightNY: false)
    }
}
