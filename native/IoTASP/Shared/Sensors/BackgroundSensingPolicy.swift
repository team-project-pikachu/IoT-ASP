import Foundation

/// Scientific-run sensing vs iOS background limits (#145).
/// Fleet AC power does **not** override OS background rules.
public enum SensingRunState: String, Sendable {
    case foreground
    case backgroundPaused
    case interrupted
}

public enum BackgroundSensingPolicy {
    /// MVP path: CoreMotion + mic only while foreground.
    public static let primaryPath = "foreground continuous CoreMotion + mic"

    public static let rejectedBackgroundModes: [String] = [
        "audio as always-on mic without a user-visible playback session",
        "location for vib science",
        "background-processing as fake always-on sensors",
    ]

    public static let justifiedIfElected: [String] = [
        "audio: only if hop TX is actually playing (not a silent keep-alive lie)",
        "bluetooth-central: not used (C1 is A2DP system route, not CoreBluetooth)",
    ]

    public static func onEnterBackground(txPlaying: Bool) -> SensingRunState {
        // Do not pretend mic continues. Pause sensing; TX may continue if audio session is playing.
        _ = txPlaying
        return .backgroundPaused
    }

    public static func onInterruption() -> SensingRunState { .interrupted }

    public static let dedicatedModeNote =
        "Keep the app foreground / Guided Access for scientific runs. See docs/iphone-dedicated-mode.md."
}
