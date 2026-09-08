import Foundation

/// Reactive louder-over-time alarm driven by acoustic detect results.
/// Maps onto fleet telemetry concepts: `alarmState`, `volBlast`, escalating target volume.
public enum NestAlarmState: String, Codable, CaseIterable, Sendable {
    case armed
    case triggered
    case sustaining
    case cleared
}

public struct EscalatingAlarmConfig: Sendable {
    public var maxVol: Double
    public var clearQuietSeconds: TimeInterval
    /// Extra step applied each tick while sustaining (gets louder).
    public var sustainStepDb: Double

    public init(maxVol: Double = 100, clearQuietSeconds: TimeInterval = 2.5, sustainStepDb: Double = 1.0) {
        self.maxVol = maxVol
        self.clearQuietSeconds = clearQuietSeconds
        self.sustainStepDb = sustainStepDb
    }
}

public final class EscalatingAlarmController: @unchecked Sendable {
    public private(set) var state: NestAlarmState = .armed
    public private(set) var volBlast = false
    public private(set) var targetVol: Double = 0
    public private(set) var lastEventClass: AcousticEventClass = .unknown
    public private(set) var holdManual = false

    private var config: EscalatingAlarmConfig
    private var quietSince: Date?

    public init(config: EscalatingAlarmConfig = EscalatingAlarmConfig()) {
        self.config = config
    }

    public func arm() {
        guard !holdManual else { return }
        state = .armed
        volBlast = false
        targetVol = 0
        quietSince = nil
    }

    public func setHoldManual(_ on: Bool) {
        holdManual = on
        if on {
            state = .cleared
            volBlast = false
            targetVol = 0
            quietSince = nil
        }
    }

    /// Apply a detector result. Glass shatter and sound burst both escalate; glass starts hotter.
    public func apply(result: AcousticDetectResult, now: Date = Date()) {
        guard !holdManual else { return }
        guard result.burst else {
            tickQuiet(now: now)
            return
        }

        lastEventClass = result.eventClass
        quietSince = nil
        volBlast = true

        let base: Double
        switch result.eventClass {
        case .glassShatter:
            base = max(targetVol, 70)
        case .soundBurst:
            base = max(targetVol, 55)
        case .unknown:
            base = max(targetVol, 40)
        }

        targetVol = min(config.maxVol, base + result.escalateDb)

        switch state {
        case .armed, .cleared:
            state = .triggered
        case .triggered:
            state = .sustaining
        case .sustaining:
            targetVol = min(config.maxVol, targetVol + config.sustainStepDb)
        }
    }

    public func tickQuiet(now: Date = Date()) {
        guard !holdManual else { return }
        guard state == .triggered || state == .sustaining else { return }
        if quietSince == nil { quietSince = now }
        let quietFor = now.timeIntervalSince(quietSince ?? now)
        if quietFor >= config.clearQuietSeconds {
            state = .armed
            volBlast = false
            // Keep a residual level briefly? Security semantics: clear blast, re-arm.
            targetVol = 0
            quietSince = nil
        } else {
            // Still in hysteresis — keep blasting and nudge louder (reactive).
            state = .sustaining
            volBlast = true
            targetVol = min(config.maxVol, targetVol + config.sustainStepDb)
        }
    }
}
