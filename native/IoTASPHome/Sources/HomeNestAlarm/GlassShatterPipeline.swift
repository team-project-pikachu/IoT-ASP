import Foundation

/// Event-triggered glass-shatter pipeline (first-class M8 feature alongside sound-burst).
/// Flow: acoustic onset → classify `glass_shatter` → Home notify/automate TODO → ASP escalate louder.
public struct GlassShatterPipeline: Sendable {
    public var detector: any BurstDetectClient
    public var alarm: EscalatingAlarmController
    public var cameras: NestCameraCatalog
    public var homeNotify: any HomeAutomationNotifyClient

    /// Human-readable TODO retained for UI / docs cross-link (#97).
    public var homeNotifyTODO: String

    public init(
        detector: any BurstDetectClient = StubBurstDetectClient(),
        alarm: EscalatingAlarmController = EscalatingAlarmController(),
        cameras: NestCameraCatalog = NestCameraCatalog(),
        homeNotify: any HomeAutomationNotifyClient = TodoHomeAutomationNotifyClient()
    ) {
        self.detector = detector
        self.alarm = alarm
        self.cameras = cameras
        self.homeNotify = homeNotify
        self.homeNotifyTODO = TodoHomeAutomationNotifyClient.todoMessage
    }

    public struct Outcome: Sendable {
        public var result: AcousticDetectResult
        public var snapshot: CameraSnapshotContext?
        public var homeNotifyPending: Bool
        public var homeNotifyAttempt: HomeNotifyAttempt?
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
        let isGlass = result.burst && result.eventClass == .glassShatter
        let snap = isGlass ? cameras.snapshotContext(for: .glassShatter) : nil
        var attempt: HomeNotifyAttempt?
        if isGlass {
            attempt = await homeNotify.notifyGlassShatter(
                cameraId: snap?.cameraId,
                confidence: result.confidence,
                escalateDb: result.escalateDb
            )
        }
        return Outcome(
            result: result,
            snapshot: snap,
            homeNotifyPending: attempt?.pending ?? false,
            homeNotifyAttempt: attempt
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
