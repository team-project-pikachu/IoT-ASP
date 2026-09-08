import Foundation

/// Event-triggered glass-shatter pipeline (first-class M8 feature alongside sound-burst).
/// Flow: acoustic onset → classify `glass_shatter` → Home notify/automate TODO → ASP escalate louder.
public struct GlassShatterPipeline: Sendable {
    public var detector: any BurstDetectClient
    public var alarm: EscalatingAlarmController
    public var cameras: NestCameraCatalog

    /// TODO(M8): Home Automation / notification hook once GoogleHomeSDK Automation API is wired.
    public var homeNotifyTODO: String

    public init(
        detector: any BurstDetectClient = StubBurstDetectClient(),
        alarm: EscalatingAlarmController = EscalatingAlarmController(),
        cameras: NestCameraCatalog = NestCameraCatalog()
    ) {
        self.detector = detector
        self.alarm = alarm
        self.cameras = cameras
        self.homeNotifyTODO = "Wire Home Automation / Nest notification for glass_shatter (owner OAuth)."
    }

    public struct Outcome: Sendable {
        public var result: AcousticDetectResult
        public var snapshot: CameraSnapshotContext?
        public var homeNotifyPending: Bool
    }

    public func handleOnset(
        energyDeltaDb: Double,
        riseMs: Double,
        source: String = "nest_cam_mic_or_asp",
        now: Date = Date()
    ) async throws -> Outcome {
        let features = AcousticEventFeatures(
            eventClassHint: .glassShatter,
            energyDeltaDb: energyDeltaDb,
            riseMs: riseMs,
            bandHint: "broadband_transient",
            source: source,
            ts: now
        )
        let result = try await detector.detect(features)
        if result.burst {
            alarm.apply(result: result, now: now)
        } else {
            alarm.tickQuiet(now: now)
        }
        let snap = result.burst && result.eventClass == .glassShatter
            ? cameras.snapshotContext(for: .glassShatter)
            : nil
        return Outcome(
            result: result,
            snapshot: snap,
            homeNotifyPending: result.eventClass == .glassShatter && result.burst
        )
    }
}

/// Combined Nest Home feature surface: sound-burst + glass-shatter share detector + escalating alarm.
public struct HomeNestAlarmPipeline: Sendable {
    public var detector: any BurstDetectClient
    public var alarm: EscalatingAlarmController
    public var glass: GlassShatterPipeline
    public var home: any HomeStructureClient

    public init(
        detector: any BurstDetectClient = StubBurstDetectClient(),
        alarm: EscalatingAlarmController = EscalatingAlarmController(),
        home: any HomeStructureClient = HomeStructureClientFactory.makeDefault()
    ) {
        self.detector = detector
        self.alarm = alarm
        self.home = home
        self.glass = GlassShatterPipeline(detector: detector, alarm: alarm)
    }

    public func handleSoundBurst(energyDeltaDb: Double, riseMs: Double, now: Date = Date()) async throws -> AcousticDetectResult {
        let features = AcousticEventFeatures(
            eventClassHint: .soundBurst,
            energyDeltaDb: energyDeltaDb,
            riseMs: riseMs,
            source: "asp_micdiff",
            ts: now
        )
        let result = try await detector.detect(features)
        if result.burst { alarm.apply(result: result, now: now) } else { alarm.tickQuiet(now: now) }
        return result
    }
}
