import SwiftUI
import HomeNestAlarm

/// Second first-class iOS feature surface (M8): Google Home / Nest + acoustic events.
/// Kept separate from the ultrasonic ASP shell (`native/IoTASP`).
public struct HomeNestRootView: View {
    @StateObject private var model = HomeNestSessionModel()

    public init() {}

    public var body: some View {
        TabView {
            // Feature 1 (sibling product surface): ASP ultrasonic / hop — deep link note only here.
            NavigationStack {
                Form {
                    Section("Sibling feature") {
                        Text("ASP ultrasonic / hop blaster lives in `native/IoTASP` (IoTASPApp).")
                            .font(.caption)
                        Text("This tab host is HomeNestAlarm — Nest cameras + Gemini acoustic events.")
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
        }
    }
}

public struct HomeNestAlarmFeatureView: View {
    @ObservedObject var model: HomeNestSessionModel

    public var body: some View {
        NavigationStack {
            Form {
                Section("Home / Nest") {
                    LabeledContent("SDK", value: model.sdkMode)
                    LabeledContent("Authorized", value: model.homeAuthorized ? "yes" : "stub / no")
                    Button("Initialize home (stub)") { Task { await model.initializeHome() } }
                    LabeledContent("Cameras", value: model.cameraIds.joined(separator: ", "))
                }
                Section("Sound burst → louder alarm") {
                    LabeledContent("alarmState", value: model.alarm.state.rawValue)
                    LabeledContent("volBlast", value: model.alarm.volBlast ? "true" : "false")
                    LabeledContent("targetVol", value: String(format: "%.1f", model.alarm.targetVol))
                    LabeledContent("lastClass", value: model.alarm.lastEventClass.rawValue)
                    Button("Simulate sound burst") { Task { await model.simulateSoundBurst() } }
                    Toggle("Hold / Manual", isOn: Binding(
                        get: { model.alarm.holdManual },
                        set: { model.setHoldManual($0) }
                    ))
                }
                Section("Owner gate") {
                    Text("OAuth / Nest premium: betty@bearresearch.io (do not commit secrets).")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("HomeNestAlarm")
        }
    }
}

public struct GlassShatterFeatureView: View {
    @ObservedObject var model: HomeNestSessionModel

    public var body: some View {
        NavigationStack {
            Form {
                Section("Glass shatter (event-triggered)") {
                    Text("Acoustic transient → classify glass_shatter → escalate louder + Nest snapshot stub.")
                        .font(.caption)
                    LabeledContent("last glass?", value: model.lastWasGlass ? "yes" : "no")
                    LabeledContent("notify TODO", value: model.homeNotifyPending ? "pending" : "idle")
                    LabeledContent("snapshot cam", value: model.lastSnapshotCam ?? "—")
                    LabeledContent("alarmState", value: model.alarm.state.rawValue)
                    LabeledContent("volBlast", value: model.alarm.volBlast ? "true" : "false")
                    Button("Simulate glass shatter") { Task { await model.simulateGlassShatter() } }
                }
                Section("Home Automation / Nest notify") {
                    Text(model.notifyTodoReason)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                    Text("Cross-link: Nest premium camera context + EscalatingAlarmController louder path (Hold/Manual clears).")
                        .font(.caption2)
                }
                Section("Shared detector") {
                    Text("Event class enum: sound_burst | glass_shatter | unknown — one Gemini/gcloud stub service.")
                        .font(.caption2)
                }
            }
            .navigationTitle("Glass Shatter")
        }
    }
}

@MainActor
public final class HomeNestSessionModel: ObservableObject {
    public let pipeline = HomeNestAlarmPipeline()
    @Published public var alarm: EscalatingAlarmController
    @Published public var cameraIds: [String] = []
    @Published public var homeAuthorized = false
    @Published public var lastWasGlass = false
    @Published public var homeNotifyPending = false
    @Published public var lastSnapshotCam: String?
    @Published public var statusMessage = ""

    public var sdkMode: String {
        #if canImport(GoogleHomeSDK)
        "GoogleHomeSDK importable"
        #else
        "stub (no GoogleHomeSDK)"
        #endif
    }

    public init() {
        self.alarm = pipeline.alarm
    }

    public func initializeHome() async {
        do {
            // Use the pipeline's HomeStructureClient (factory selects live vs stub).
            // Demo button may upgrade an unauthorized stub so the UI can list cameras without OAuth.
            var client = pipeline.home
            if let stub = client as? StubHomeStructureClient, !stub.isAuthorized {
                client = StubHomeStructureClient(isAuthorized: true, stubCameraIds: stub.stubCameraIds)
            }
            try await client.initializeHome()
            cameraIds = try await client.listCameraDeviceIds()
            homeAuthorized = client.isAuthorized
            statusMessage = "home initialized via pipeline client"
        } catch {
            homeAuthorized = false
            statusMessage = String(describing: error)
        }
    }

    public func setHoldManual(_ on: Bool) {
        alarm.setHoldManual(on)
        objectWillChange.send()
    }

    public func simulateSoundBurst() async {
        do {
            _ = try await pipeline.handleSoundBurst(energyDeltaDb: 12, riseMs: 150)
            alarm = pipeline.alarm
            lastWasGlass = pipeline.alarm.lastEventClass == .glassShatter
        } catch {
            statusMessage = String(describing: error)
        }
    }

    public func simulateGlassShatter() async {
        do {
            let outcome = try await pipeline.glass.handleOnset(energyDeltaDb: 14, riseMs: 40)
            alarm = pipeline.alarm
            lastWasGlass = outcome.result.eventClass == .glassShatter
            homeNotifyPending = outcome.homeNotifyPending
            lastSnapshotCam = outcome.snapshot?.cameraId
        } catch {
            statusMessage = String(describing: error)
        }
    }
}
