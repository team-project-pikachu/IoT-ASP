import Foundation

/// Product-event mapping used by telemetry / Nest-Glass hooks — not iPhone chrome.
/// Command center is the Vercel blaster (or the macOS wrapper of that URL).
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
    /// Public SDD surface (C3). iPhone is a node; this URL is the command center.
    public static let commandCenterURLString = "https://hop-ultrasonic-1digital-design.vercel.app/"
    public static var commandCenterURL: URL { URL(string: commandCenterURLString)! }

    public static let tabs: [NativeAppTab] = NativeAppTab.allCases
    public static let tabTitles: [String] = NativeAppTab.allCases.map(\.title)
    public static let constraintBanner =
        "C1 A2DP TX only. No Web Bluetooth. SensorKit stub until Apple grant. Nest OAuth parked."

    public static func armSensorsImplies() -> [String] {
        ["permissions", "coremotion", "ultrasonic-mic"]
    }

    /// Phone/Watch operator line — Hold wins, then pause, then off, then alert, else on.
    public static func statusLine(on: Bool, hold: Bool, paused: Bool, alert: Bool) -> String {
        if hold { return "Hold" }
        if paused { return "Paused" }
        if !on { return "Off" }
        if alert { return "Alert" }
        return "On"
    }
}
