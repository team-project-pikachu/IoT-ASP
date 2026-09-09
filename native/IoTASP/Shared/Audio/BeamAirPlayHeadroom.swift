import Foundation

/// Digital peak headroom for AirPlay → Sonos Beam Gen 2.
///
/// Field symptom on Mac Studio (M4 Max) → AirPlay → Beam above ~60%
/// macOS/AirPlay system volume with near-FS content: clicking, clipping,
/// and **staticky/crackle** (digital overs / hard limiting).
/// Not a Sonos-published 60% SPL spec — see
/// `docs/sonos-beam-gen2-airplay-volume-constraints.md`.
///
/// Policy history: 0.60 (−4.4 dBFS) reduced residual click but did not clear it;
/// 0.50 (−6.0 dBFS) adds ~1.6 dB more send-path headroom under UI 100% (C4).
///
/// UI / patch may still show 100% (C4); map carrier amplitude through `peakGain`.
public enum BeamAirPlayHeadroom {
    /// Linear peak relative to full-scale (−6.0 dBFS). Keep in sync with
    /// `AIRPLAY_BEAM_PEAK` in `public/index.html`.
    public static let peakGain: Float = 0.50
}
