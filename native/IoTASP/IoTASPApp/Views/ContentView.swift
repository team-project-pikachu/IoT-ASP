import SwiftUI

struct ContentView: View {
    @EnvironmentObject var session: ASPSessionModel

    var body: some View {
        TabView {
            HopTabView()
                .tabItem { Label(NativeAppTab.hop.title, systemImage: NativeAppTab.hop.systemImage) }
            NestAlarmTabView()
                .tabItem { Label(NativeAppTab.nestAlarm.title, systemImage: NativeAppTab.nestAlarm.systemImage) }
            GlassShatterTabView()
                .tabItem { Label(NativeAppTab.glassShatter.title, systemImage: NativeAppTab.glassShatter.systemImage) }
            SystemsCheckView()
                .tabItem { Label(NativeAppTab.systems.title, systemImage: NativeAppTab.systems.systemImage) }
        }
    }
}
