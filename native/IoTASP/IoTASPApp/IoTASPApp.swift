import SwiftUI

@main
struct IoTASPApp: App {
    @StateObject private var session = ASPSessionModel()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(session)
                .onAppear { session.bootstrap() }
        }
    }
}
