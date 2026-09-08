import Foundation

/// First-run / re-arm permission order for hop scientific runs (#144).
/// SensorKit is **never** requested unless the entitled compile flag is on.
public enum PermissionKind: String, CaseIterable, Sendable, Codable {
    case microphone
    case motion
    case sensorkit
}

public enum PermissionState: String, Sendable, Codable {
    case notDetermined
    case denied
    case restricted
    case authorized
    case skippedUngated
}

public struct PermissionStep: Equatable, Sendable {
    public var kind: PermissionKind
    public var state: PermissionState
    public var prePrompt: String

    public init(kind: PermissionKind, state: PermissionState, prePrompt: String) {
        self.kind = kind
        self.state = state
        self.prePrompt = prePrompt
    }

    public var isBlocking: Bool {
        state == .denied || state == .restricted
    }
}

public enum PermissionSequencer {
    /// Explain → mic → motion. SensorKit appended only when entitled.
    public static func sequence(sensorkitEntitled: Bool) -> [PermissionKind] {
        var steps: [PermissionKind] = [.microphone, .motion]
        if sensorkitEntitled {
            steps.append(.sensorkit)
        }
        return steps
    }

    public static func prePrompt(for kind: PermissionKind) -> String {
        switch kind {
        case .microphone:
            return "Mic is used for micDiff / 17–23 kHz band energy. Audio is metered on-device; it is not uploaded."
        case .motion:
            return "Motion is used for 1–100 Hz vib science (intense 10–20 Hz proxy). CoreMotion, not SensorKit."
        case .sensorkit:
            return "SensorKit runs only if Apple granted com.apple.developer.sensorkit.reader.allow for a research study."
        }
    }

    public static func usageDescription(for kind: PermissionKind) -> String {
        switch kind {
        case .microphone:
            return "IoT-ASP meters the microphone for micDiff impulse detection and 17–23 kHz hop-band energy. Audio stays on-device."
        case .motion:
            return "IoT-ASP logs accelerometer and gyroscope for 1–100 Hz vibration science (intense 10–20 Hz band)."
        case .sensorkit:
            return "IoT-ASP reads SensorKit streams only when Apple has approved a research study for this App ID."
        }
    }

    public static func initialSteps(sensorkitEntitled: Bool) -> [PermissionStep] {
        sequence(sensorkitEntitled: sensorkitEntitled).map { kind in
            PermissionStep(kind: kind, state: .notDetermined, prePrompt: prePrompt(for: kind))
        }
    }

    public static func apply(state: PermissionState, to kind: PermissionKind, steps: [PermissionStep]) -> [PermissionStep] {
        steps.map { step in
            guard step.kind == kind else { return step }
            return PermissionStep(kind: step.kind, state: state, prePrompt: step.prePrompt)
        }
    }

    public static func ungatedSensorKitStep() -> PermissionStep {
        PermissionStep(
            kind: .sensorkit,
            state: .skippedUngated,
            prePrompt: prePrompt(for: .sensorkit)
        )
    }

    public static func statusLine(_ steps: [PermissionStep]) -> String {
        steps.map { "\($0.kind.rawValue)=\($0.state.rawValue)" }.joined(separator: ", ")
    }
}
