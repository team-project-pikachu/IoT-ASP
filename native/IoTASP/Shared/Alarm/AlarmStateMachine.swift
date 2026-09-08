import Foundation

/// Alarm-system reactivity for ASP hop blaster.
/// Cite: docs/algorithms.md § Impulse → blast / alarm state machine
public enum AlarmState: String, Codable, CaseIterable, Sendable {
    case armed
    case triggered
    case sustaining
    case cleared
}

public struct AlarmConfig: Sendable {
    /// Quiet hysteresis before leaving sustaining → cleared (seconds).
    public var clearQuietSeconds: TimeInterval = 2.5
    /// Max UI volume blast target (C4). Night window may cap via `nightTargetVol`.
    public var blastVol: Double = 100
    /// Night glide step when escalating from quiet (C5 night curve).
    public var nightStep: Double = 0.5
    public var nightTargetVol: Double = 100

    public init() {}
}

public struct ImpulseEvent: Sendable {
    public var fromAccel: Bool
    public var fromMicDiff: Bool
    public var riseMs: Double
    public var ts: Date

    public init(fromAccel: Bool, fromMicDiff: Bool, riseMs: Double, ts: Date = Date()) {
        self.fromAccel = fromAccel
        self.fromMicDiff = fromMicDiff
        self.riseMs = riseMs
        self.ts = ts
    }

    public var isImpulse: Bool { fromAccel || fromMicDiff }
}

/// Fast arm → trigger → escalate → sustain while impulse train continues → clear only after quiet hysteresis.
public final class AlarmStateMachine: @unchecked Sendable {
    public private(set) var state: AlarmState = .cleared
    public private(set) var volBlast = false
    public private(set) var impulse = false
    public private(set) var holdManual = false
    public private(set) var targetVol: Double = 100

    private var config: AlarmConfig
    private var lastImpulseAt: Date?
    private var quietSince: Date?

    public init(config: AlarmConfig = AlarmConfig()) {
        self.config = config
    }

    public func arm() {
        guard !holdManual else { return }
        state = .armed
        volBlast = false
        impulse = false
        quietSince = nil
    }

    /// Hold / Manual wins — disarm and freeze blast.
    public func setHoldManual(_ on: Bool) {
        holdManual = on
        if on {
            state = .cleared
            volBlast = false
            impulse = false
            quietSince = nil
        }
    }

    public func tick(now: Date = Date(), impulseEvent: ImpulseEvent?, nightNY: Bool) {
        if holdManual { return }

        if let e = impulseEvent, e.isImpulse {
            impulse = true
            lastImpulseAt = now
            quietSince = nil
            switch state {
            case .cleared, .armed:
                state = .triggered
                blast(now: now, nightNY: nightNY, immediate: true)
            case .triggered:
                state = .sustaining
                blast(now: now, nightNY: nightNY, immediate: true)
            case .sustaining:
                blast(now: now, nightNY: nightNY, immediate: true)
            }
            return
        }

        impulse = false
        guard state == .triggered || state == .sustaining else { return }

        if quietSince == nil { quietSince = now }
        let quietFor = now.timeIntervalSince(quietSince ?? now)
        if quietFor >= config.clearQuietSeconds {
            state = .cleared
            volBlast = false
            quietSince = nil
        } else {
            state = .sustaining
            volBlast = true
        }
    }

    private func blast(now: Date, nightNY: Bool, immediate: Bool) {
        volBlast = true
        if nightNY && !immediate {
            targetVol = min(config.nightTargetVol, targetVol + config.nightStep)
        } else {
            // Security-alarm jump toward max (clamped).
            targetVol = nightNY ? min(config.blastVol, config.nightTargetVol) : config.blastVol
        }
    }

    public var telemetry: [String: Any] {
        [
            "alarmState": state.rawValue,
            "impulse": impulse,
            "volBlast": volBlast,
            "holdManual": holdManual,
            "vol": targetVol,
        ]
    }
}
