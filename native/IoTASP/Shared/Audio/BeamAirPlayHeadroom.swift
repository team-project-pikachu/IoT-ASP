import Foundation

/// Digital peak headroom for AirPlay → Sonos Beam Gen 2.
///
/// Field symptom on Mac Studio (M4 Max) → AirPlay → Beam above ~60%
/// macOS/AirPlay system volume with near-FS content: clicking, clipping,
/// and **staticky/crackle** (digital overs / hard limiting).
/// Not a Sonos-published 60% SPL spec — see
/// `docs/sonos-beam-gen2-airplay-volume-constraints.md`.
///
/// UI / patch may still show 100% (C4); map carrier amplitude through `peakGain`.
public enum BeamAirPlayHeadroom {
    /// Linear peak relative to full-scale (−4.4 dBFS).
    public static let peakGain: Float = 0.60
}
