import XCTest
@testable import HomeNestAlarm

final class HomeNestAlarmTests: XCTestCase {
    func testWireRawValuesAgreeWithPython() {
        XCTAssertEqual(AcousticEventClass.soundBurst.rawValue, "sound_burst")
        XCTAssertEqual(AcousticEventClass.glassShatter.rawValue, "glass_shatter")
        XCTAssertEqual(AcousticEventClass.unknown.rawValue, "unknown")
    }

    func testStubThresholdsSoundBurst() async throws {
        let client = StubBurstDetectClient()
        let r = try await client.detect(
            AcousticEventFeatures(eventClassHint: .soundBurst, energyDeltaDb: 12, riseMs: 150)
        )
        XCTAssertTrue(r.burst)
        XCTAssertEqual(r.eventClass, .soundBurst)
        XCTAssertEqual(r.escalateDb, 2.0, accuracy: 0.001)
    }

    func testStubThresholdsGlassShatter() async throws {
        let client = StubBurstDetectClient()
        let r = try await client.detect(
            AcousticEventFeatures(eventClassHint: .glassShatter, energyDeltaDb: 14, riseMs: 40)
        )
        XCTAssertTrue(r.burst)
        XCTAssertEqual(r.eventClass, .glassShatter)
        XCTAssertEqual(r.escalateDb, 4.0, accuracy: 0.001)
    }

    func testBoundaryRiseMsGlassVsBurst() async throws {
        let client = StubBurstDetectClient()
        let glass = try await client.detect(
            AcousticEventFeatures(eventClassHint: .glassShatter, energyDeltaDb: 14, riseMs: 80)
        )
        let burst = try await client.detect(
            AcousticEventFeatures(eventClassHint: .glassShatter, energyDeltaDb: 14, riseMs: 81)
        )
        XCTAssertEqual(glass.eventClass, .glassShatter)
        XCTAssertEqual(burst.eventClass, .soundBurst)
    }

    func testColdBelowOnset() async throws {
        let client = StubBurstDetectClient()
        let r = try await client.detect(
            AcousticEventFeatures(eventClassHint: .glassShatter, energyDeltaDb: 3, riseMs: 20)
        )
        XCTAssertFalse(r.burst)
        XCTAssertEqual(r.eventClass, .unknown)
        XCTAssertEqual(r.escalateDb, 0, accuracy: 0.001)
    }
}
