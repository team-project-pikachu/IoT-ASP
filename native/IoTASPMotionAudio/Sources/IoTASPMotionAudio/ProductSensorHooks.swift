import Foundation

/// Combined onset event that HomeNestAlarm / Glass Shatter / hop alarm can consume
/// without importing GoogleHomeSDK or the #109 app shell.
public struct ProductSensorOnset: Sendable, Equatable {
    public enum Kind: String, Sendable {
        case motionImpulse
        case micDiff
        case glassShatterHint
        case soundBurstHint
    }

    public var kind: Kind
    public var energyDelta: Double
    public var riseMs: Double
    public var absA: Double
    public var source: String
    public var ts: Date

    public init(
        kind: Kind,
        energyDelta: Double,
        riseMs: Double = 40,
        absA: Double = 0,
        source: String,
        ts: Date = Date()
    ) {
        self.kind = kind
        self.energyDelta = energyDelta
        self.riseMs = riseMs
        self.absA = absA
        self.source = source
        self.ts = ts
    }
}

public protocol ProductSensorOnsetSink: AnyObject {
    func ingestProductOnset(_ onset: ProductSensorOnset)
}

/// Bridges CoreMotion + mic stubs into M8-style product flows (energyDeltaDb / impulse).
public final class ProductSensorHooks: @unchecked Sendable {
    public weak var sink: ProductSensorOnsetSink?
    public var micDiffOnsetDb: Double = 9
    public var accelOnset: Double = 0.45

    private var accelBaseline: Double = 0.05
    private var micBaseline: Double = -80

    public init(sink: ProductSensorOnsetSink? = nil) {
        self.sink = sink
    }

    public func observeMotion(_ sample: MotionSample) {
        guard sample.available else { return }
        let ema = 0.9 * accelBaseline + 0.1 * sample.absA
        let delta = sample.absA - accelBaseline
        accelBaseline = ema
        guard delta >= accelOnset else { return }
        sink?.ingestProductOnset(ProductSensorOnset(
            kind: .motionImpulse,
            energyDelta: delta,
            riseMs: 40,
            absA: sample.absA,
            source: sample.source,
            ts: sample.ts
        ))
    }

    public func observeMic(_ sample: MicEnergySample) {
        guard sample.available else { return }
        let ema = 0.9 * micBaseline + 0.1 * sample.energyDb
        let delta = sample.energyDb - micBaseline
        micBaseline = ema
        guard delta >= micDiffOnsetDb else { return }
        let kind: ProductSensorOnset.Kind =
            delta >= micDiffOnsetDb * 1.5 ? .glassShatterHint : .soundBurstHint
        sink?.ingestProductOnset(ProductSensorOnset(
            kind: kind,
            energyDelta: delta,
            riseMs: 40,
            absA: 0,
            source: sample.source,
            ts: sample.ts
        ))
    }

    /// Explicit micDiff onset for Nest / Glass Shatter pipelines (`energyDeltaDb`, `riseMs`).
    public func emitMicDiffHint(energyDeltaDb: Double, riseMs: Double = 40, glass: Bool = false) {
        sink?.ingestProductOnset(ProductSensorOnset(
            kind: glass ? .glassShatterHint : .micDiff,
            energyDelta: energyDeltaDb,
            riseMs: riseMs,
            source: glass ? "glass_shatter_hint" : "micdiff_hint"
        ))
    }
}
