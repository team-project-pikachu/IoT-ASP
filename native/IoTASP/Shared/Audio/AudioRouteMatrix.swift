import Foundation

/// TX/RX route matrix for hop C1 (#146). Default: A2DP TX + **phone mic** RX (not HFP).
public struct AudioRoutePlan: Equatable, Sendable {
    public var sink: FleetSink
    public var category: String
    public var mode: String
    public var options: [String]
    public var micAvailable: Bool
    public var hfpRisk: Bool
    public var note: String

    public init(sink: FleetSink, category: String, mode: String, options: [String], micAvailable: Bool, hfpRisk: Bool, note: String) {
        self.sink = sink
        self.category = category
        self.mode = mode
        self.options = options
        self.micAvailable = micAvailable
        self.hfpRisk = hfpRisk
        self.note = note
    }
}

public enum AudioRouteMatrix {
    /// C1: never Web Bluetooth. HFP is rejected for carrier TX.
    public static func plan(for sink: FleetSink, micArmed: Bool) -> AudioRoutePlan {
        switch sink {
        case .soundcore2A2DP:
            return AudioRoutePlan(
                sink: sink,
                category: micArmed ? "playAndRecord" : "playback",
                mode: micArmed ? "measurement" : "default",
                options: ["allowBluetoothA2DP"],
                micAvailable: micArmed,
                hfpRisk: false,
                note: "A2DP TX + phone mic RX. Do not switch to HFP for speaker mic."
            )
        case .phoneSpeaker:
            return AudioRoutePlan(
                sink: sink,
                category: micArmed ? "playAndRecord" : "playback",
                mode: micArmed ? "measurement" : "default",
                options: ["defaultToSpeaker"],
                micAvailable: micArmed,
                hfpRisk: false,
                note: "Built-in speaker TX; phone mic RX. Not C1 fleet default."
            )
        case .sonosBeamAirPlay:
            return AudioRoutePlan(
                sink: sink,
                category: "playback",
                mode: "default",
                options: ["longFormAudio"],
                micAvailable: micArmed,
                hfpRisk: false,
                note: "AirPlay long-form to Beam (#39). Not A2DP C1 parity. Mic stays on phone."
            )
        }
    }

    public static func recoverAfterRouteChange(_ sink: FleetSink) -> String {
        "Re-apply plan(for: \(sink.rawValue)); if BT dropped, fall back to phoneSpeaker without silent failure."
    }
}
