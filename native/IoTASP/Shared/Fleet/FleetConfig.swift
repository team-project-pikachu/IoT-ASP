import Foundation

/// Fleet topology for native shell. Soundcore manufacturer FR/power: TODO → issue #43 / docs/hardware/soundcore-2.md
public enum FleetSink: String, Codable, Sendable {
    case soundcore2A2DP = "soundcore2_a2dp"
    case sonosBeamAirPlay = "sonos_beam_airplay"
    case phoneSpeaker = "phone_speaker"
}

public struct FleetNode: Sendable {
    public var id: String
    public var sink: FleetSink
    public var role: String

    public static let defaults: [FleetNode] = [
        FleetNode(id: "node1", sink: .soundcore2A2DP, role: "Room A — iPhone 16 ↔ Soundcore 2 (A2DP C1)"),
        FleetNode(id: "node2", sink: .soundcore2A2DP, role: "Room B — iPhone 16 ↔ Soundcore 2 (A2DP C1)"),
        FleetNode(id: "node3", sink: .sonosBeamAirPlay, role: "Node 3 — iPhone 16 ↔ Sonos Beam Gen 2 (AirPlay 2, #39)"),
    ]

    public init(id: String, sink: FleetSink, role: String) {
        self.id = id
        self.sink = sink
        self.role = role
    }
}

public enum SoundcoreConstraints {
    /// Placeholder until #43 lands official Anker/Soundcore citations.
    public static let ratedPowerWattsTODO = 12.0
    public static let ultrasonicHonesty =
        "Expect AAC/SBC + BassUp/DSP roll-off in 17–23 kHz; do not claim flat FR."
    public static let lf10_20Honesty =
        "10–20 Hz TX typically na on Soundcore/A2DP; gate lfDriveCapable; intense vib sensing still via accel."
    public static let docsTODO = "docs/hardware/soundcore-2.md (issue #43)"
}
