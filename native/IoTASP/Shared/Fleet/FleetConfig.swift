import Foundation

/// Fleet topology for native shell.
/// Soundcore manufacturer dossier: `docs/hardware/soundcore-specs.md` (#43) — not live lab FR.
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
        FleetNode(id: "node1", sink: .soundcore2A2DP, role: "Room A — iPhone 16 ↔ Soundcore 2 A3105 (A2DP C1)"),
        FleetNode(id: "node2", sink: .soundcore2A2DP, role: "Room B — iPhone 16 ↔ Soundcore 2 A3105 (A2DP C1)"),
        FleetNode(id: "node3", sink: .sonosBeamAirPlay, role: "Node 3 — iPhone ↔ Sonos Beam Gen 2 AirPlay (#39; not A2DP)"),
    ]

    public init(id: String, sink: FleetSink, role: String) {
        self.id = id
        self.sink = sink
        self.role = role
    }
}

public enum SoundcoreConstraints {
    /// Published peak stereo power (6 W × 2) — Anker/Soundcore product pages; see soundcore-specs.md.
    public static let ratedPowerWattsPublished = 12.0
    /// Ultrasonic honesty: manufacturer FR for 17–23 kHz is **unpublished**; do not claim flat FR.
    public static let ultrasonicHonesty =
        "A3105 FR unpublished; expect AAC/SBC + BassUp/DSP roll-off in 17–23 kHz; no flat-FR claim."
    public static let lf10_20Honesty =
        "10–20 Hz TX typically na on Soundcore/A2DP; gate lfDriveCapable=false; intense vib via accel only."
    public static let docsPath = "docs/hardware/soundcore-specs.md (+ soundcore-2.md pointer)"
    @available(*, deprecated, renamed: "ratedPowerWattsPublished")
    public static let ratedPowerWattsTODO = ratedPowerWattsPublished
    @available(*, deprecated, renamed: "docsPath")
    public static let docsTODO = docsPath
}
