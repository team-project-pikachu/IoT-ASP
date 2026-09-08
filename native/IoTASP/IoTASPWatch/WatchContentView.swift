import SwiftUI

struct WatchContentView: View {
    @EnvironmentObject var model: WatchSessionModel

    var body: some View {
        VStack(spacing: 8) {
            Text("IoT-ASP")
                .font(.headline)
            Text(model.alarmState)
                .font(.caption)
            Text(model.volBlast ? "BLAST" : "idle")
                .foregroundStyle(model.volBlast ? .red : .secondary)
            Button("Impulse") { model.sendImpulse() }
            Button(model.hold ? "Resume" : "Hold / Manual") { model.toggleHold() }
            Text("Hold wins. Nest OAuth parked.")
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .padding()
    }
}
