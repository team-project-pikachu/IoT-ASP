import Foundation

#if canImport(CoreMotion)
import CoreMotion
#endif

/// CoreMotion shell slot (#109) for ultrasonic / hop vib surfaces.
/// Implementation package: sibling #111 → `native/IoTASPMotionAudio` (when merged).
public struct CoreMotionShellModule: AppShellModule {
    public let id = "coremotion"
    public let title = "Motion"
    public let systemImage = "gyroscope"

    public init() {}

    public var frameworkLinked: Bool {
        #if canImport(CoreMotion)
        true
        #else
        false
        #endif
    }

    public var modeLabel: String {
        frameworkLinked
            ? "CoreMotion linkable (simulator-safe stub in #111)"
            : "stub (CoreMotion unavailable on this SDK)"
    }

    public var statusSummary: String {
        "Placeholder tab. Sample stream + permission live in #111 MotionStreamStub. Requires NSMotionUsageDescription (see docs/privacy-entitlements-native.md / #113)."
    }
}
