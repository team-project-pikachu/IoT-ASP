import SwiftUI

struct ContentView: View {
    @EnvironmentObject var session: ASPSessionModel

    var body: some View {
        NavigationStack {
            Form {
                Section("Fleet sink") {
                    Picker("Node sink", selection: $session.sink) {
                        Text("Soundcore 2 A2DP").tag(FleetSink.soundcore2A2DP)
                        Text("Sonos Beam AirPlay").tag(FleetSink.sonosBeamAirPlay)
                        Text("Phone speaker").tag(FleetSink.phoneSpeaker)
                    }
                    Text(SoundcoreConstraints.docsTODO)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }

                Section("Alarm") {
                    LabeledContent("State", value: session.alarm.state.rawValue)
                    LabeledContent("impulse", value: session.alarm.impulse ? "true" : "false")
                    LabeledContent("volBlast", value: session.alarm.volBlast ? "true" : "false")
                    LabeledContent("vol", value: String(format: "%.1f", session.alarm.targetVol))
                    Toggle("Hold / Manual", isOn: Binding(
                        get: { session.alarm.holdManual },
                        set: { session.setHold($0) }
                    ))
                    Button("Arm alarm") { session.arm() }
                    Button("Simulate impulse") { session.simulateImpulse() }
                }

                Section("Sensors") {
                    Toggle("Arm CoreMotion 1–100 Hz", isOn: $session.motionArmed)
                    LabeledContent("|a|", value: String(format: "%.3f", session.lastAbsA))
                    LabeledContent("intense 10–20 Hz proxy", value: session.intenseVib ? "yes" : "no")
                    LabeledContent("SensorKit linked", value: SensorKitGate.isLinked ? "yes" : "no")
                    LabeledContent("SensorKit entitled", value: SensorKitGate.entitlementDeclared ? "yes" : "stub")
                }

                Section("Route") {
                    RoutePickerRepresentable()
                        .frame(height: 44)
                    Text("C1 carrier TX requires A2DP. AirPlay is a parked Sonos research exception. Web cannot SensorKit.")
                        .font(.caption2)
                }
            }
            .navigationTitle("IoT-ASP")
        }
    }
}
