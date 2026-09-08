import Foundation

/// M9 app-shell module contract (#109).
/// Placeholders only — full SensorKit / CoreMotion / mic libs land in sibling issues
/// (#110 `native/IoTASPSensorKit`, #111 `native/IoTASPMotionAudio`).
public protocol AppShellModule: Sendable {
    /// Stable id for tabs / Systems-check rows.
    var id: String { get }
    /// Human-readable title (UI tab).
    var title: String { get }
    /// SF Symbol name for the tab item.
    var systemImage: String { get }
    /// Compile / entitlement honesty label (never invents Apple grants).
    var modeLabel: String { get }
    /// Short status for the shell UI.
    var statusSummary: String { get }
}

/// Catalog of M9 shell modules hosted by `AppShellRootView`.
public enum AppShellCatalog {
    public static let modules: [any AppShellModule] = [
        SensorKitShellModule(),
        CoreMotionShellModule(),
        MicAVFoundationShellModule(),
    ]

    public static var ids: [String] {
        modules.map(\.id)
    }
}
