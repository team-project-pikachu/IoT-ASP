import Foundation

/// Native leftover honesty for #25. Full AEC and LF mic remain HW-limited.
/// Do **not** close #25 from this PR (`Related`, not Fixes).
public enum NativeAECHonesty {
    public static let fullAEC = false
    public static let lfMic = false
    public static let path = "output-bus-subtraction + measurement mode (not voice-processing I/O)"
    public static let alpha = UltrasonicMicMeter.micDiffAlpha

    public static func report() -> [String: String] {
        [
            "fullAEC": "false",
            "lfMic": "false",
            "path": path,
            "alpha": String(alpha),
            "issue": "25",
            "blocksRedeploy": "false",
        ]
    }
}
