import Foundation

/// Protocol for Gemini Enterprise (gcloud / Vertex) burst + glass-shatter detection.
/// Live calls are owner-gated (1Password `dev` + betty@bearresearch.io). Stub never hits network.
public protocol BurstDetectClient: Sendable {
    func detect(_ features: AcousticEventFeatures) async throws -> AcousticDetectResult
}

/// Offline heuristic stub — shares one interface for `sound_burst` and `glass_shatter`.
public struct StubBurstDetectClient: BurstDetectClient {
    public var onsetDb: Double
    public var glassRiseMsMax: Double

    public init(onsetDb: Double = 9.0, glassRiseMsMax: Double = 80.0) {
        self.onsetDb = onsetDb
        self.glassRiseMsMax = glassRiseMsMax
    }

    public func detect(_ features: AcousticEventFeatures) async throws -> AcousticDetectResult {
        let hot = features.energyDeltaDb >= onsetDb
        guard hot else {
            return AcousticDetectResult(burst: false, eventClass: .unknown, confidence: 0.1, escalateDb: 0)
        }

        let classified: AcousticEventClass
        switch features.eventClassHint {
        case .glassShatter:
            classified = features.riseMs <= glassRiseMsMax ? .glassShatter : .soundBurst
        case .soundBurst:
            classified = .soundBurst
        case .unknown:
            // Short sharp onset → glass-shatter-like; otherwise generic burst.
            classified = features.riseMs <= glassRiseMsMax ? .glassShatter : .soundBurst
        }

        let confidence: Double
        let escalate: Double
        switch classified {
        case .glassShatter:
            confidence = min(0.95, 0.55 + features.energyDeltaDb / 40.0)
            escalate = 4.0
        case .soundBurst:
            confidence = min(0.9, 0.45 + features.energyDeltaDb / 50.0)
            escalate = 2.0
        case .unknown:
            confidence = 0.2
            escalate = 1.0
        }

        return AcousticDetectResult(
            burst: true,
            eventClass: classified,
            confidence: confidence,
            escalateDb: escalate
        )
    }
}
