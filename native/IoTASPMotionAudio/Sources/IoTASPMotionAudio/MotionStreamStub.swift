import Foundation

#if canImport(CoreMotion) && (os(iOS) || os(watchOS))
import CoreMotion
#endif

/// Motion sample for hop / Nest product surfaces (no UIKit dependency).
public struct MotionSample: Sendable, Equatable {
    public var ax: Double
    public var ay: Double
    public var az: Double
    public var gx: Double
    public var gy: Double
    public var gz: Double
    public var available: Bool
    public var source: String
    public var ts: Date

    public init(
        ax: Double = 0,
        ay: Double = 0,
        az: Double = 0,
        gx: Double = 0,
        gy: Double = 0,
        gz: Double = 0,
        available: Bool,
        source: String,
        ts: Date = Date()
    ) {
        self.ax = ax
        self.ay = ay
        self.az = az
        self.gx = gx
        self.gy = gy
        self.gz = gz
        self.available = available
        self.source = source
        self.ts = ts
    }

    public var absA: Double {
        (ax * ax + ay * ay + az * az).squareRoot()
    }

    public static func unavailable(reason: String = "motion_unavailable", ts: Date = Date()) -> MotionSample {
        MotionSample(available: false, source: reason, ts: ts)
    }
}

public protocol MotionSampleSink: AnyObject {
    func ingestMotionSample(_ sample: MotionSample)
}

/// Simulator-safe CoreMotion stream. Never crashes when device motion is missing (CI / macOS / Simulator).
/// Live `CMMotionManager` is iOS/watchOS-only (`API_UNAVAILABLE(macos)`); macOS CI always uses stub path.
public final class MotionStreamStub: @unchecked Sendable {
    public private(set) var last: MotionSample?
    public weak var sink: MotionSampleSink?
    public var onSample: ((MotionSample) -> Void)?
    public private(set) var isRunning = false

    /// When true, emit synthetic samples even if CoreMotion is unavailable (unit tests / CI).
    public var allowSyntheticFallback: Bool

    #if canImport(CoreMotion) && (os(iOS) || os(watchOS))
    private var motion: CMMotionManager?
    #endif

    public init(allowSyntheticFallback: Bool = false) {
        self.allowSyntheticFallback = allowSyntheticFallback
    }

    public var isDeviceMotionAvailable: Bool {
        #if canImport(CoreMotion) && (os(iOS) || os(watchOS))
        return CMMotionManager().isDeviceMotionAvailable
        #else
        return false
        #endif
    }

    /// Request path is a no-op on platforms without a motion permission UI.
    /// Call before `start` so app shells can mirror iOS privacy UX.
    public func requestPermissionIfNeeded(completion: @escaping (Bool) -> Void) {
        // CoreMotion does not expose a separate async permission API for device motion;
        // NSMotionUsageDescription on the app target covers the privacy string.
        completion(isDeviceMotionAvailable || allowSyntheticFallback)
    }

    public func start(hz: Double = 50) {
        stop()
        isRunning = true
        let interval = 1.0 / min(100, max(1, hz))

        #if canImport(CoreMotion) && (os(iOS) || os(watchOS))
        let mgr = CMMotionManager()
        guard mgr.isDeviceMotionAvailable else {
            motion = nil
            emitUnavailableOrSynthetic(reason: "device_motion_unavailable")
            return
        }
        mgr.deviceMotionUpdateInterval = interval
        mgr.startDeviceMotionUpdates(to: .main) { [weak self] data, _ in
            guard let self, self.isRunning else { return }
            guard let d = data else {
                self.emit(.unavailable(reason: "motion_nil_sample"))
                return
            }
            let a = d.userAcceleration
            let r = d.rotationRate
            self.emit(MotionSample(
                ax: a.x, ay: a.y, az: a.z,
                gx: r.x, gy: r.y, gz: r.z,
                available: true,
                source: "coremotion"
            ))
        }
        motion = mgr
        #else
        _ = interval
        emitUnavailableOrSynthetic(reason: "coremotion_unavailable_on_platform")
        #endif
    }

    public func stop() {
        isRunning = false
        #if canImport(CoreMotion) && (os(iOS) || os(watchOS))
        motion?.stopDeviceMotionUpdates()
        motion = nil
        #endif
    }

    /// Test / CI helper: push one sample without CoreMotion.
    public func injectSynthetic(_ sample: MotionSample) {
        emit(sample)
    }

    private func emitUnavailableOrSynthetic(reason: String) {
        if allowSyntheticFallback {
            emit(MotionSample(
                ax: 0.01, ay: 0, az: 0,
                available: true,
                source: "synthetic_fallback"
            ))
        } else {
            emit(.unavailable(reason: reason))
        }
        isRunning = false
    }

    private func emit(_ sample: MotionSample) {
        last = sample
        onSample?(sample)
        sink?.ingestMotionSample(sample)
    }
}
