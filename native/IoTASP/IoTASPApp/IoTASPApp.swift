import SwiftUI

@main
struct IoTASPApp: App {
    @StateObject private var session = ASPSessionModel()
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(session)
                .onAppear { session.bootstrap() }
        }
        .onChange(of: scenePhase) { phase in
            session.handleScenePhaseActive(phase == .active)
        }
    }
}
