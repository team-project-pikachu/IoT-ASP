import SwiftUI

/// Primary hop / ASP control surface.
struct HopTabView: View {
    @EnvironmentObject var session: ASPSessionModel

    var body: some View {
        NavigationStack {
            Form {
                Section("Fleet") {
                    Picker("Node sink", selection: $session.sink) {
                        Text("Soundcore 2 A2DP").tag(FleetSink.soundcore2A2DP)
                        Text("Sonos Beam AirPlay").tag(FleetSink.sonosBeamAirPlay)
                        Text("Phone speaker").tag(FleetSink.phoneSpeaker)
                    }
                    LabeledContent("active route", value: session.activeRouteLabel)
                    Text(SoundcoreConstraints.ultrasonicHonesty)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                    RoutePickerRepresentable()
                        .frame(height: 44)
                }

                Section("Arm") {
                    Button(session.sensorsArmed ? "Disarm sensors" : "Arm sensors") {
                        session.sensorsArmed ? session.disarmSensors() : session.armSensors()
                    }
                    LabeledContent("sensing", value: session.sensingState.rawValue)
                    LabeledContent("motion", value: session.motionArmed ? "on" : "off")
                    LabeledContent("mic 48 kHz", value: session.micArmed ? "on" : "off")
                    if let err = session.sessionError {
                        Text(err).font(.caption).foregroundStyle(.red)
                    }
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

                Section("Vib") {
                    Picker("materialPreset", selection: $session.materialPreset) {
                        Text("table").tag(MaterialPreset.table)
                        Text("speaker").tag(MaterialPreset.speaker)
                        Text("handheld").tag(MaterialPreset.handheld)
                        Text("chair").tag(MaterialPreset.chair)
                    }
                    LabeledContent("vibClass", value: session.vibClass)
                    LabeledContent("|a| (g)", value: String(format: "%.3f", session.lastAbsA))
                    LabeledContent("physical", value: session.lastPhysicalEvent)
                    LabeledContent("acoustic", value: session.lastAcousticEvent)
                }
            }
            .navigationTitle("Hop")
        }
    }
}
