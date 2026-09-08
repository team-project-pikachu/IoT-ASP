import AVFoundation
import Foundation

/// Playback session for A2DP (Soundcore) or AirPlay (Sonos Beam #39).
/// When mic is armed, Soundcore/phoneSpeaker use playAndRecord + measurement (A2DP option, not HFP).
public enum ASPAudioSession {
    public static func configureForFleetSink(_ sink: FleetSink) throws {
        try configureForFleetSink(sink, micArmed: false)
    }

    public static func configureForFleetSink(_ sink: FleetSink, micArmed: Bool) throws {
        let session = AVAudioSession.sharedInstance()
        let plan = AudioRouteMatrix.plan(for: sink, micArmed: micArmed)
        switch sink {
        case .soundcore2A2DP:
            if micArmed {
                try session.setCategory(.playAndRecord, mode: .measurement, options: [.allowBluetoothA2DP, .mixWithOthers])
            } else {
                try session.setCategory(.playback, mode: .default, options: [.allowBluetoothA2DP])
            }
        case .phoneSpeaker:
            if micArmed {
                try session.setCategory(.playAndRecord, mode: .measurement, options: [.defaultToSpeaker, .mixWithOthers])
            } else {
                try session.setCategory(.playback, mode: .default, options: [.defaultToSpeaker])
            }
        case .sonosBeamAirPlay:
            try session.setCategory(.playback, mode: .default, policy: .longFormAudio)
        }
        try session.setActive(true)
        _ = plan
    }

    public static func currentSinkLabel() -> String {
        let outs = AVAudioSession.sharedInstance().currentRoute.outputs
        if outs.isEmpty { return "none" }
        return outs.map { $0.portType.rawValue }.joined(separator: ",")
    }
}
