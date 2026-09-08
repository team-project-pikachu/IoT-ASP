import XCTest
@testable import IoTASPMotionAudio

final class MotionAudioStubTests: XCTestCase {
    func testMotionUnavailableDoesNotCrash() {
        let stream = MotionStreamStub(allowSyntheticFallback: false)
        stream.requestPermissionIfNeeded { ok in
            // On CLT/macOS without device motion, ok may be false — still must not crash.
            _ = ok
        }
        stream.start(hz: 50)
        stream.stop()
        XCTAssertNotNil(stream.last)
        XCTAssertEqual(stream.last?.available, false)
    }

    func testSyntheticMotionFallback() {
        let stream = MotionStreamStub(allowSyntheticFallback: true)
        // Force synthetic path when hardware absent.
        if !stream.isDeviceMotionAvailable {
            stream.start(hz: 10)
            XCTAssertEqual(stream.last?.source, "synthetic_fallback")
            XCTAssertEqual(stream.last?.available, true)
        }
        stream.injectSynthetic(MotionSample(ax: 0.5, available: true, source: "inject"))
        XCTAssertEqual(stream.last?.ax, 0.5)
        stream.stop()
    }

    func testMicStubIdleSafe() {
        let mic = MicCaptureStub(stubOnly: true)
        var perm: MicPermissionState = .undetermined
        let exp = expectation(description: "perm")
        mic.requestPermission { state in
            perm = state
            exp.fulfill()
        }
        wait(for: [exp], timeout: 1)
        XCTAssertEqual(perm, .granted)
        mic.start()
        XCTAssertEqual(mic.last?.available, false)
        mic.stop()
    }

    func testProductHooksGlassAndMotion() {
        final class Sink: ProductSensorOnsetSink {
            var events: [ProductSensorOnset] = []
            func ingestProductOnset(_ onset: ProductSensorOnset) { events.append(onset) }
        }
        let sink = Sink()
        let hooks = ProductSensorHooks(sink: sink)
        hooks.observeMotion(MotionSample(ax: 1.0, available: true, source: "t"))
        hooks.emitMicDiffHint(energyDeltaDb: 12, glass: true)
        XCTAssertFalse(sink.events.isEmpty)
        XCTAssertTrue(sink.events.contains { $0.kind == .glassShatterHint })
    }
}
