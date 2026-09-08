import AVFoundation
import Foundation

/// Playback session for A2DP (Soundcore) or AirPlay (Sonos Beam #39).
public enum ASPAudioSession {
    public static func configureForFleetSink(_ sink: FleetSink) throws {
        let session = AVAudioSession.sharedInstance()
        switch sink {
        case .soundcore2A2DP, .phoneSpeaker:
            try session.setCategory(.playback, mode: .default, options: [.allowBluetoothA2DP])
        case .sonosBeamAirPlay:
            try session.setCategory(.playback, mode: .default, policy: .longFormAudio)
        }
        try session.setActive(true)
    }
}
