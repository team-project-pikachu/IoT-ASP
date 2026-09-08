import Foundation

/// Shared detector event taxonomy for Gemini Enterprise / local stubs (M8).
/// Distinct classes share one service interface; glass shatter is event-triggered, not generic burst.
public enum AcousticEventClass: String, Codable, CaseIterable, Sendable {
    case soundBurst = "sound_burst"
    case glassShatter = "glass_shatter"
    case unknown = "unknown"
}

/// Feature vector / event payload sent to the burst-detect stub (no raw audio required in stub mode).
public struct AcousticEventFeatures: Codable, Sendable {
    public var eventClassHint: AcousticEventClass
    public var energyDeltaDb: Double
    public var riseMs: Double
    public var bandHint: String?
    public var source: String
    public var ts: Date

    public init(
        eventClassHint: AcousticEventClass = .unknown,
        energyDeltaDb: Double,
        riseMs: Double,
        bandHint: String? = nil,
        source: String = "asp_micdiff",
        ts: Date = Date()
    ) {
        self.eventClassHint = eventClassHint
        self.energyDeltaDb = energyDeltaDb
        self.riseMs = riseMs
        self.bandHint = bandHint
        self.source = source
        self.ts = ts
    }
}

/// Detector response — drives ASP `volBlast` / escalating alarm.
public struct AcousticDetectResult: Codable, Sendable {
    public var burst: Bool
    public var eventClass: AcousticEventClass
    public var confidence: Double
    /// Suggested volume escalation step (dB-equivalent UI units) while sustaining.
    public var escalateDb: Double

    public init(burst: Bool, eventClass: AcousticEventClass, confidence: Double, escalateDb: Double) {
        self.burst = burst
        self.eventClass = eventClass
        self.confidence = confidence
        self.escalateDb = escalateDb
    }
}
