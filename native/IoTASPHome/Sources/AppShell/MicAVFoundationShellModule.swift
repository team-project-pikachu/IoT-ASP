import Foundation

#if canImport(AVFoundation)
import AVFoundation
#endif

/// AVFoundation mic shell slot (#109) for micDiff / glass / Nest acoustic hooks.
/// Implementation package: sibling #111 → `native/IoTASPMotionAudio` (when merged).
public struct MicAVFoundationShellModule: AppShellModule {
    public let id = "avfoundation-mic"
    public let title = "Mic"
    public let systemImage = "mic"

    public init() {}

    public var frameworkLinked: Bool {
        #if canImport(AVFoundation)
        true
        #else
        false
        #endif
    }

    public var modeLabel: String {
        frameworkLinked
            ? "AVFoundation linkable (session stub in #111)"
            : "stub (AVFoundation unavailable on this SDK)"
    }

    public var statusSummary: String {
        "Placeholder tab. Mic / AVAudioSession path lives in #111 MicCaptureStub. Requires NSMicrophoneUsageDescription — no Nest/OAuth tokens here."
    }
}
