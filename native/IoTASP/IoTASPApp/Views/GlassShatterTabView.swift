import SwiftUI

/// Glass Shatter product tab — same micDiff/burst path, not a shatter classifier.
struct GlassShatterTabView: View {
    @EnvironmentObject var session: ASPSessionModel

    var body: some View {
        NavigationStack {
            Form {
                Section("Honesty") {
                    Text("Native demo maps acoustic burst → sound_burst. This is not a glass-shatter ML classifier.")
                        .font(.caption)
                    LabeledContent("mic bandEnergyUs", value: String(format: "%.1f dB", session.micStatus.lastBandEnergyUs))
                    LabeledContent("acoustic event", value: session.lastAcousticEvent)
                    LabeledContent("AEC", value: NativeAECHonesty.fullAEC ? "full" : "best-effort / off")
                }
                Section("Demo") {
                    Button("Simulate burst → alarm") { session.demoProductEvent(.sound_burst) }
                    LabeledContent("alarm", value: session.alarm.state.rawValue)
                }
            }
            .navigationTitle("Glass Shatter")
        }
    }
}
