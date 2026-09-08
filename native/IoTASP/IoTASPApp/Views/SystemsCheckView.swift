import SwiftUI

/// Systems-check / diagnostics (on-device plan #151).
struct SystemsCheckView: View {
    @EnvironmentObject var session: ASPSessionModel

    var body: some View {
        NavigationStack {
            Form {
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
                }

                Section("CoreMotion") {
                    LabeledContent("accel", value: yn(session.motionAvailability.accelerometer))
                    LabeledContent("gyro", value: yn(session.motionAvailability.gyroscope))
                    LabeledContent("mag", value: yn(session.motionAvailability.magnetometer))
                    LabeledContent("deviceMotion", value: yn(session.motionAvailability.deviceMotion))
                    LabeledContent("altimeter", value: yn(session.motionAvailability.altimeter))
                    LabeledContent("pedometer", value: "skip")
                    LabeledContent("plan Hz", value: String(format: "%.0f", session.motionPlanHz))
                    LabeledContent("|a|", value: String(format: "%.3f g", session.lastAbsA))
                    LabeledContent("|ω|", value: String(format: "%.3f", session.lastAbsOmega))
                    LabeledContent("intense 10–20 Hz", value: session.intenseVib ? "yes" : "no")
                    LabeledContent("lfEnergy felt proxy", value: String(format: "%.1f dB", session.lfEnergyDb))
                    Text(LfAccelProxy.honesty).font(.caption2)
                }

                Section("Mic 17–23 kHz") {
                    LabeledContent("preferred Hz", value: String(format: "%.0f", session.micStatus.preferredSampleRate))
                    LabeledContent("granted Hz", value: String(format: "%.0f", session.micStatus.grantedSampleRate))
                    LabeledContent("US Nyquist OK", value: yn(session.micStatus.usBandOk))
                    LabeledContent("AEC off requested", value: yn(session.micStatus.aecOffRequested))
                    LabeledContent("OS may override", value: session.micStatus.osMayOverride ? "yes" : "no")
                    Text(session.micStatus.note).font(.caption2)
                }

                Section("SensorKit") {
                    LabeledContent("linked", value: yn(SensorKitGate.isLinked))
                    LabeledContent("entitled", value: SensorKitGate.entitlementDeclared ? "yes" : "stub")
                    LabeledContent("start", value: SensorKitReaderMap.start(entitled: false))
                }

                Section("Other sensors") {
                    LabeledContent("ambient light", value: "unavailable (no public API)")
                    ForEach(OtherSensorsGate.table(altimeterHardware: session.motionAvailability.altimeter), id: \.kind) { row in
                        LabeledContent(row.kind.rawValue, value: row.statusCopy)
                    }
                }

                Section("Telemetry") {
                    TextField("telemetry URL (empty = no POST)", text: $session.telemetryURL)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                    TextField("patch URL (empty = skip poll)", text: $session.patchURL)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                    LabeledContent("POST enabled", value: yn(TelemetryBridge.shouldPost(telemetryURL: session.telemetryURL)))
                    LabeledContent("last heartbeat", value: session.lastHeartbeatOK ? "ok" : "none")
                    LabeledContent("schemaVersion", value: "\(TelemetryBridge.schemaVersion)")
                }

                Section("Background") {
                    LabeledContent("run state", value: session.sensingState.rawValue)
                    Text(BackgroundSensingPolicy.dedicatedModeNote).font(.caption2)
                    Text(NativeAppShell.constraintBanner).font(.caption2)
                }
            }
            .navigationTitle("Systems")
        }
    }

    private func yn(_ v: Bool) -> String { v ? "yes" : "no" }
}
