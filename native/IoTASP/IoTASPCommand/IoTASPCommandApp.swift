import SwiftUI

@main
struct IoTASPCommandApp: App {
    var body: some Scene {
        WindowGroup("HOP command center") {
            CommandCenterWebView(url: NativeAppShell.commandCenterURL)
                .frame(minWidth: 780, minHeight: 720)
        }
        .defaultSize(width: 820, height: 980)
    }
}
