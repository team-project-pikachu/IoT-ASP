import Foundation

/// Digital peak headroom for AirPlay → Sonos Beam Gen 2.
///
/// Field: Mac Studio (M4 Max) → AirPlay → Beam Gen 2 still **clips** at UI 100%
/// with peak 0.60 (−4.4 dBFS). Policy is **0.40** (−8.0 dBFS) — field-driven
/// send-path headroom, not a Sonos-published SPL spec. See
/// `docs/sonos-beam-gen2-airplay-volume-constraints.md`.
///
/// UI / patch may still show 100% (C4); map carrier amplitude through `peakGain`.
public enum BeamAirPlayHeadroom {
    /// Linear peak relative to full-scale (−8.0 dBFS). Keep in sync with
    /// `AIRPLAY_BEAM_PEAK` in `public/index.html`.
    public static let peakGain: Float = 0.40
}
