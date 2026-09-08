import XCTest
@testable import HomeNestAlarm

final class HomeNestAlarmTests: XCTestCase {

    func testWireRawValuesAgreeWithPython() {
        XCTAssertEqual(AcousticEventClass.soundBurst.rawValue, "sound_burst")
        XCTAssertEqual(AcousticEventClass.glassShatter.rawValue, "glass_shatter")
        XCTAssertEqual(AcousticEventClass.unknown.rawValue, "unknown")
    }

    func testHomeNotifyTodoPendingOnGlass() async throws {
        let pipe = GlassShatterPipeline()
        let out = try await pipe.handleOnset(energyDeltaDb: 15, riseMs: 35)
        XCTAssertTrue(out.homeNotifyPending)
        XCTAssertEqual(out.homeNotifyAttempt?.delivered, false)
        XCTAssertTrue(out.homeNotifyAttempt?.todoReason.contains("#97") == true)
    }
    func testSoundBurstEscalatesLouder() async throws {
        let alarm = EscalatingAlarmController()
        let client = StubBurstDetectClient()
        let features = AcousticEventFeatures(eventClassHint: .soundBurst, energyDeltaDb: 12, riseMs: 120)
        let r1 = try await client.detect(features)
        XCTAssertTrue(r1.burst)
        XCTAssertEqual(r1.eventClass, .soundBurst)
        alarm.apply(result: r1)
        let v1 = alarm.targetVol
        alarm.apply(result: r1)
        XCTAssertGreaterThan(alarm.targetVol, v1)
        XCTAssertTrue(alarm.volBlast)
    }

    func testGlassShatterClassAndHotStart() async throws {
        let pipe = GlassShatterPipeline()
        let out = try await pipe.handleOnset(energyDeltaDb: 15, riseMs: 35)
        XCTAssertTrue(out.result.burst)
        XCTAssertEqual(out.result.eventClass, .glassShatter)
        XCTAssertTrue(out.homeNotifyPending)
        XCTAssertNotNil(out.snapshot)
        XCTAssertGreaterThanOrEqual(pipe.alarm.targetVol, 70)
    }

    func testHomeFacadeStubUnauthorized() async {
        let home = StubHomeStructureClient(isAuthorized: false)
        do {
            try await home.initializeHome()
            XCTFail("expected unauthorized")
        } catch HomeSDKError.unauthorized {
            // expected
        } catch {
            XCTFail("unexpected \(error)")
        }
    }

    func testHoldManualClearsAndBlocksReescalate() async throws {
        let alarm = EscalatingAlarmController()
        let client = StubBurstDetectClient()
        let features = AcousticEventFeatures(eventClassHint: .soundBurst, energyDeltaDb: 12, riseMs: 120)
        let r1 = try await client.detect(features)
        alarm.apply(result: r1)
        XCTAssertTrue(alarm.volBlast)
        alarm.setHoldManual(true)
        XCTAssertFalse(alarm.volBlast)
        XCTAssertEqual(alarm.state, .cleared)
        XCTAssertEqual(alarm.targetVol, 0, accuracy: 0.001)
        alarm.apply(result: r1)
        XCTAssertFalse(alarm.volBlast)
        XCTAssertEqual(alarm.state, .cleared)
        XCTAssertEqual(alarm.targetVol, 0, accuracy: 0.001)
    }

    func testSnapshotPrefersSupportsSnapshotCamera() {
        let catalog = NestCameraCatalog(devices: [
            NestCameraDevice(id: "no-snap", displayName: "Audio only", supportsAudio: true, supportsSnapshot: false),
            NestCameraDevice(id: "snap-cam", displayName: "With snapshot", supportsAudio: true, supportsSnapshot: true),
        ])
        let ctx = catalog.snapshotContext(for: .glassShatter)
        XCTAssertEqual(ctx?.cameraId, "snap-cam")
    }

}
