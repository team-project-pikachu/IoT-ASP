import Foundation

#if canImport(CoreMotion)
import CoreMotion
#endif

#if canImport(Combine)
import Combine
#endif

#if canImport(CoreMotion) && canImport(Combine)
@MainActor
public final class PhoneMotionLogger: ObservableObject {
    private let motion = CMMotionManager()
    public private(set) var last: VibSample?
    public var onSample: ((VibSample) -> Void)?

    public init() {}

    public func start(hz: Double = 50) {
        guard motion.isDeviceMotionAvailable else { return }
        motion.deviceMotionUpdateInterval = 1.0 / min(100, max(1, hz))
        motion.startDeviceMotionUpdates(to: .main) { [weak self] data, _ in
            guard let d = data else { return }
            let a = d.userAcceleration
            let r = d.rotationRate
            let sample = VibSample(ax: a.x, ay: a.y, az: a.z, gx: r.x, gy: r.y, gz: r.z)
            self?.last = sample
            self?.onSample?(sample)
        }
    }

    public func stop() {
        motion.stopDeviceMotionUpdates()
    }
}
#endif
