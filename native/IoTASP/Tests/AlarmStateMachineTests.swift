import XCTest
@testable import IoTASPShared

final class AlarmStateMachineTests: XCTestCase {
    func testImpulseTriggersBlast() {
        let m = AlarmStateMachine()
        m.arm()
        XCTAssertEqual(m.state, .armed)
        let e = ImpulseEvent(fromAccel: true, fromMicDiff: false, riseMs: 40)
        m.tick(now: Date(), impulseEvent: e, nightNY: false)
        XCTAssertEqual(m.state, .triggered)
        XCTAssertTrue(m.volBlast)
        XCTAssertTrue(m.impulse)
        XCTAssertEqual(m.targetVol, 100)
    }

    func testHoldWins() {
        let m = AlarmStateMachine()
        m.arm()
        m.setHoldManual(true)
        let e = ImpulseEvent(fromAccel: true, fromMicDiff: false, riseMs: 40)
        m.tick(now: Date(), impulseEvent: e, nightNY: false)
        XCTAssertEqual(m.state, .cleared)
        XCTAssertFalse(m.volBlast)
    }

    func testQuietHysteresisBeforeClear() {
        let m = AlarmStateMachine()
        m.arm()
        let t0 = Date()
        m.tick(now: t0, impulseEvent: ImpulseEvent(fromAccel: true, fromMicDiff: false, riseMs: 20), nightNY: false)
        XCTAssertEqual(m.state, .triggered)
        m.tick(now: t0.addingTimeInterval(0.5), impulseEvent: nil, nightNY: false)
        XCTAssertEqual(m.state, .sustaining)
        m.tick(now: t0.addingTimeInterval(3.0), impulseEvent: nil, nightNY: false)
        XCTAssertEqual(m.state, .cleared)
        XCTAssertFalse(m.volBlast)

        m.tick(now: t0.addingTimeInterval(3.1), impulseEvent: ImpulseEvent(fromAccel: false, fromMicDiff: true, riseMs: 20), nightNY: false)
        XCTAssertEqual(m.state, .triggered)
    }

    func testFleetHasSoundcoreAndSonos() {
        let sinks = Set(FleetNode.defaults.map(\.sink))
        XCTAssertTrue(sinks.contains(.soundcore2A2DP))
        XCTAssertTrue(sinks.contains(.sonosBeamAirPlay))
    }

    func testBeamAirPlayHeadroomPeak() {
        XCTAssertEqual(BeamAirPlayHeadroom.peakGain, 0.50, accuracy: 0.0001)
    }
}
