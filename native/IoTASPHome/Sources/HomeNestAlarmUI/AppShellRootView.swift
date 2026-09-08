import SwiftUI
import AppShell
import HomeNestAlarm

/// M9 successor app shell (#109): M8 Nest/Glass product tabs **plus**
/// SensorKit / CoreMotion / Mic module placeholders for later #110 / #111 wiring.
///
/// Prefer this over `HomeNestRootView` for new product work. M8 view remains for
/// Nest-only demos and Playgrounds snippets.
public struct AppShellRootView: View {
    @StateObject private var model = HomeNestSessionModel()
    private let sensorKit = SensorKitShellModule()
    private let motion = CoreMotionShellModule()
    private let mic = MicAVFoundationShellModule()

    public init() {}

    public var body: some View {
        TabView {
            NavigationStack {
                Form {
                    Section("Sibling feature") {
                        Text("ASP ultrasonic / hop blaster lives in `native/IoTASP` (IoTASPApp).")
                            .font(.caption)
                        Text("This host is IoTASPHome AppShell — M8 Nest/Glass + M9 sensor module slots.")
                            .font(.caption)
                    }
                }
                .navigationTitle("ASP Ultrasonic")
            }
            .tabItem { Label("ASP Ultrasonic", systemImage: "waveform") }

            HomeNestAlarmFeatureView(model: model)
                .tabItem { Label("Home Nest Alarm", systemImage: "house") }

            GlassShatterFeatureView(model: model)
                .tabItem { Label("Glass Shatter", systemImage: "exclamationmark.triangle") }

            AppShellModulePlaceholderView(module: sensorKit)
                .tabItem { Label(sensorKit.title, systemImage: sensorKit.systemImage) }

            AppShellModulePlaceholderView(module: motion)
                .tabItem { Label(motion.title, systemImage: motion.systemImage) }

            AppShellModulePlaceholderView(module: mic)
                .tabItem { Label(mic.title, systemImage: mic.systemImage) }
        }
    }
}

/// Shared placeholder UI for M9 module tabs (no live SensorKit / mic capture).
public struct AppShellModulePlaceholderView: View {
    private let moduleTitle: String
    private let moduleId: String
    private let modeLabel: String
    private let statusSummary: String

    public init(module: any AppShellModule) {
        self.moduleTitle = module.title
        self.moduleId = module.id
        self.modeLabel = module.modeLabel
        self.statusSummary = module.statusSummary
    }

    public var body: some View {
        NavigationStack {
            Form {
                Section("Module") {
                    LabeledContent("id", value: moduleId)
                    LabeledContent("mode", value: modeLabel)
                }
                Section("Status") {
                    Text(statusSummary)
                        .font(.caption)
                }
                Section("Constraints") {
                    Text("No invented OAuth / Nest client IDs. No SensorKit entitlement uncomment without human Apple approval (#113).")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle(moduleTitle)
        }
    }
}
