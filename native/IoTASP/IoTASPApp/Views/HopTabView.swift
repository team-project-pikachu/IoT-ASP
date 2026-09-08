import SwiftUI

/// Phone node: power + what’s going on. Hop / Nest / Glass / Systems live on the command center.
struct HopTabView: View {
    @EnvironmentObject var session: ASPSessionModel

    var body: some View {
        ZStack {
            Color(red: 20 / 255, green: 21 / 255, blue: 25 / 255)
                .ignoresSafeArea()
            VStack(spacing: 28) {
                Text("HOP")
                    .font(.system(size: 13, weight: .semibold))
                    .tracking(3.6)
                    .foregroundStyle(Color(red: 118 / 255, green: 124 / 255, blue: 140 / 255))

                Text(session.operatorStatus)
                    .font(.system(size: 56, weight: .regular, design: .monospaced))
                    .foregroundStyle(statusColor)
                    .accessibilityLabel("Status \(session.operatorStatus)")

                Button(action: togglePower) {
                    Text(session.sensorsArmed ? "On" : "Off")
                        .font(.system(size: 15, weight: .semibold))
                        .tracking(2.4)
                        .textCase(.uppercase)
                        .frame(width: 128, height: 128)
                        .foregroundStyle(session.sensorsArmed
                            ? Color(red: 227 / 255, green: 168 / 255, blue: 1)
                            : Color(red: 118 / 255, green: 124 / 255, blue: 140 / 255))
                        .background(
                            RoundedRectangle(cornerRadius: 14, style: .continuous)
                                .fill(Color(red: 29 / 255, green: 31 / 255, blue: 39 / 255))
                        )
                        .overlay(
                            RoundedRectangle(cornerRadius: 14, style: .continuous)
                                .stroke(session.sensorsArmed
                                    ? Color(red: 157 / 255, green: 92 / 255, blue: 1)
                                    : Color(red: 51 / 255, green: 55 / 255, blue: 71 / 255), lineWidth: 1)
                        )
                }
                .buttonStyle(.plain)
                .accessibilityLabel(session.sensorsArmed ? "On" : "Off")

                Toggle("Hold / Manual", isOn: Binding(
                    get: { session.alarm.holdManual },
                    set: { session.setHold($0) }
                ))
                .tint(Color(red: 157 / 255, green: 92 / 255, blue: 1))
                .padding(.horizontal, 32)

                Link("Command center", destination: NativeAppShell.commandCenterURL)
                    .font(.system(size: 15, weight: .medium))
                    .foregroundStyle(Color(red: 157 / 255, green: 92 / 255, blue: 1))

                if let err = session.sessionError {
                    Text(err)
                        .font(.caption)
                        .foregroundStyle(.red)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }
            }
            .padding()
        }
    }

    private var statusColor: Color {
        switch session.operatorStatus {
        case "Alert": return Color(red: 1, green: 162 / 255, blue: 58 / 255)
        case "On": return Color(red: 123 / 255, green: 224 / 255, blue: 168 / 255)
        case "Hold": return Color(red: 227 / 255, green: 168 / 255, blue: 1)
        default: return Color(red: 200 / 255, green: 204 / 255, blue: 216 / 255)
        }
    }

    private func togglePower() {
        if session.sensorsArmed {
            session.disarmSensors()
        } else {
            session.armSensors()
        }
    }
}
