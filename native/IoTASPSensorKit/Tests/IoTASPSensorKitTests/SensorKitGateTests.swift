import XCTest
@testable import IoTASPSensorKit

final class SensorKitGateTests: XCTestCase {
    func testStubModeNeverClaimsEntitlement() {
        XCTAssertFalse(SensorKitGate.entitlementDeclared)
        XCTAssertEqual(SensorKitGate.modeLabel == "entitled", false)
    }

    func testStartReadersIsNoOpInStub() {
        SensorKitGate.startReadersIfEntitled()
        let sample = SensorKitGate.latestStubSample()
        XCTAssertFalse(sample.entitled)
        XCTAssertEqual(sample.source, "sensorkit_stub")
    }

    func testProductHookEmitsStub() {
        final class Sink: SensorKitOnsetSink {
            var last: SensorKitSample?
            func ingestSensorKitSample(_ sample: SensorKitSample) { last = sample }
        }
        let sink = Sink()
        let hook = SensorKitProductHook(sink: sink)
        hook.emitStubPulse()
        XCTAssertEqual(sink.last?.source, "sensorkit_stub")
        XCTAssertEqual(sink.last?.entitled, false)
    }
}
