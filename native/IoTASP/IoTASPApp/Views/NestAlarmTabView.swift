import SwiftUI

/// Home / Nest alarm product tab. Nest OAuth is parked — local alarm only.
struct NestAlarmTabView: View {
    @EnvironmentObject var session: ASPSessionModel

    var body: some View {
        NavigationStack {
            Form {
                Section("Google Home / Nest") {
                    LabeledContent("OAuth", value: ProductTabHooks.nestOAuthParked ? "parked" : "live")
                    Text("No Nest client IDs or tokens in this app. Burst events drive the local AlarmStateMachine.")
                        .font(.caption)
                }
                Section("Event") {
                    LabeledContent("product class", value: session.productEvent.rawValue)
                    LabeledContent("suggested tab", value: ProductTabHooks.tab(for: session.productEvent).rawValue)
                    LabeledContent("alarm", value: session.alarm.state.rawValue)
                    LabeledContent("volBlast", value: session.alarm.volBlast ? "true" : "false")
                }
                Section("Demo") {
                    Button("Simulate sound_burst") { session.demoProductEvent(.sound_burst) }
                    Toggle("Hold / Manual", isOn: Binding(
                        get: { session.alarm.holdManual },
                        set: { session.setHold($0) }
                    ))
                }
            }
            .navigationTitle("Nest Alarm")
        }
    }
}
