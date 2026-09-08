import Foundation

/// Native iOS app chrome (#109 successor): product tabs + Arm-sensors contract.
public enum NativeAppTab: String, CaseIterable, Sendable {
    case hop
    case nestAlarm
    case glassShatter
    case systems

    public var title: String {
        switch self {
        case .hop: return "Hop"
        case .nestAlarm: return "Nest Alarm"
        case .glassShatter: return "Glass Shatter"
        case .systems: return "Systems"
        }
    }

    public var systemImage: String {
        switch self {
        case .hop: return "waveform"
        case .nestAlarm: return "house"
        case .glassShatter: return "exclamationmark.triangle"
        case .systems: return "checkmark.circle"
        }
    }
}

public struct NativeAppShell {
    public static let tabs: [NativeAppTab] = NativeAppTab.allCases
    public static let tabTitles: [String] = NativeAppTab.allCases.map(\.title)
    public static let constraintBanner =
        "C1 A2DP TX only. No Web Bluetooth. SensorKit stub until Apple grant. Nest OAuth parked."

    public static func armSensorsImplies() -> [String] {
        ["permissions", "coremotion", "ultrasonic-mic"]
    }
}
