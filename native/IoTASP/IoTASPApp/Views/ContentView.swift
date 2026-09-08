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
                    LabeledContent("|a| (g)", value: String(format: "%.3f", session.lastAbsA))
                    LabeledContent("physical vib", value: session.lastPhysicalEvent)
                    LabeledContent("shake count", value: "\(session.shakeCount)")
                    LabeledContent("|ω|", value: String(format: "%.3f", session.lastAbsOmega))
                    LabeledContent("plan Hz", value: String(format: "%.0f", session.motionPlanHz))
                    LabeledContent("accel", value: session.motionAvailability.accelerometer ? "yes" : "no")
                    LabeledContent("gyro", value: session.motionAvailability.gyroscope ? "yes" : "no")
                    LabeledContent("mag (optional)", value: session.motionAvailability.magnetometer ? "yes" : "no")
                    LabeledContent("deviceMotion", value: session.motionAvailability.deviceMotion ? "yes" : "no")
                    LabeledContent("altimeter", value: session.motionAvailability.altimeter ? "yes" : "no")
                    LabeledContent("pedometer", value: "skip (not hop-vib)")
                    LabeledContent("intense 10–20 Hz proxy", value: session.intenseVib ? "yes" : "no")
                    LabeledContent("SensorKit linked", value: SensorKitGate.isLinked ? "yes" : "no")
                    LabeledContent("SensorKit entitled", value: SensorKitGate.entitlementDeclared ? "yes" : "stub")
                }

                Section("Permissions") {
                    ForEach(session.permissionSteps, id: \.kind) { step in
                        VStack(alignment: .leading, spacing: 2) {
                            LabeledContent(step.kind.rawValue, value: step.state.rawValue)
                            Text(step.prePrompt)
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                    }
                    Button("Re-arm permissions") { session.runPermissionSequence() }
                    Text("Denied mic/motion does not crash; SensorKit is skipped unless Apple granted the reader entitlement.")
                        .font(.caption2)
                }

                Section("Near-ultrasonic mic") {
                    Toggle("Arm 48 kHz mic (AEC/NS/AGC off)", isOn: $session.micArmed)
                    LabeledContent("preferred Hz", value: String(format: "%.0f", session.micStatus.preferredSampleRate))
                    LabeledContent("granted Hz", value: String(format: "%.0f", session.micStatus.grantedSampleRate))
                    LabeledContent("US Nyquist OK", value: session.micStatus.usBandOk ? "yes" : "no")
                    LabeledContent("AEC off requested", value: session.micStatus.aecOffRequested ? "yes" : "no")
                    LabeledContent("OS may override", value: session.micStatus.osMayOverride ? "yes (honest)" : "no")
                    LabeledContent("bandEnergyUs", value: String(format: "%.1f dB", session.micStatus.lastBandEnergyUs))
                    Text(session.micStatus.note)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
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
