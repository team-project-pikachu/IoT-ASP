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
    #if canImport(CoreMotion)
    private let altimeter = CMAltimeter()
    #endif
    public private(set) var last: VibSample?
    public private(set) var lastFull: FullMotionSample?
    public private(set) var availability = MotionAvailability.simulatorSafe
    public private(set) var activePlan = MotionStreamPlan()
    public var onSample: ((VibSample) -> Void)?
    public var onFullSample: ((FullMotionSample) -> Void)?

    public init() {
        probeAvailability()
    }

    /// Honest hardware probe — all false on Simulator / when APIs report unavailable.
    public func probeAvailability() {
        var a = MotionAvailability.simulatorSafe
        a.accelerometer = motion.isAccelerometerAvailable
        a.gyroscope = motion.isGyroAvailable
        a.magnetometer = motion.isMagnetometerAvailable
        a.deviceMotion = motion.isDeviceMotionAvailable
        a.pedometer = false // never armed (#140 skip)
        a.altimeter = CMAltimeter.isRelativeAltitudeAvailable()
        availability = a
    }

    public func start(hz: Double = 50) {
        start(plan: MotionStreamPlan.scientific(availability: availability, hz: hz))
    }

    public func start(plan: MotionStreamPlan) {
        stop()
        probeAvailability()
        let hz = CoreMotionSuite.clampHz(plan.hz)
        let interval = CoreMotionSuite.interval(hz: hz)
        var armed = plan
        armed.hz = hz
        // Never start streams the hardware does not advertise.
        armed.rawAccelerometer = plan.rawAccelerometer && availability.accelerometer
        armed.rawGyroscope = plan.rawGyroscope && availability.gyroscope
        armed.magnetometer = plan.magnetometer && availability.magnetometer
        armed.deviceMotion = plan.deviceMotion && availability.deviceMotion
        armed.altimeter = plan.altimeter && availability.altimeter
        activePlan = armed

        if armed.deviceMotion {
            motion.deviceMotionUpdateInterval = interval
            motion.startDeviceMotionUpdates(to: .main) { [weak self] data, _ in
                guard let self, let d = data else { return }
                let a = d.userAcceleration
                let r = d.rotationRate
                let g = d.gravity
                let att = d.attitude
                var full = self.lastFull ?? FullMotionSample()
                full.ax = a.x
                full.ay = a.y
                full.az = a.z
                full.gx = r.x
                full.gy = r.y
                full.gz = r.z
                full.gravityX = g.x
                full.gravityY = g.y
                full.gravityZ = g.z
                full.roll = att.roll
                full.pitch = att.pitch
                full.yaw = att.yaw
                full.ts = Date()
                self.publish(full)
            }
        }

        // Raw accel/gyro fill axes only when fused deviceMotion is unavailable.
        // deviceMotion.userAcceleration is gravity-excluded (preferred, #4 / #140).
        if armed.rawAccelerometer && !armed.deviceMotion {
            motion.accelerometerUpdateInterval = interval
            motion.startAccelerometerUpdates(to: .main) { [weak self] data, _ in
                guard let self, let d = data else { return }
                var full = self.lastFull ?? FullMotionSample()
                full.ax = d.acceleration.x
                full.ay = d.acceleration.y
                full.az = d.acceleration.z
                full.ts = Date()
                self.publish(full)
            }
        } else if armed.rawAccelerometer {
            motion.accelerometerUpdateInterval = interval
            motion.startAccelerometerUpdates(to: .main) { _, _ in
                // Hardware armed for systems-check; fused deviceMotion owns ax/ay/az.
            }
        }

        if armed.rawGyroscope && !armed.deviceMotion {
            motion.gyroUpdateInterval = interval
            motion.startGyroUpdates(to: .main) { [weak self] data, _ in
                guard let self, let d = data else { return }
                var full = self.lastFull ?? FullMotionSample()
                full.gx = d.rotationRate.x
                full.gy = d.rotationRate.y
                full.gz = d.rotationRate.z
                full.ts = Date()
                self.publish(full)
            }
        } else if armed.rawGyroscope {
            motion.gyroUpdateInterval = interval
            motion.startGyroUpdates(to: .main) { _, _ in }
        }

        if armed.magnetometer {
            motion.magnetometerUpdateInterval = interval
            motion.startMagnetometerUpdates(to: .main) { [weak self] data, _ in
                guard let self, let d = data else { return }
                var full = self.lastFull ?? FullMotionSample()
                full.mx = d.magneticField.x
                full.my = d.magneticField.y
                full.mz = d.magneticField.z
                full.ts = Date()
                self.lastFull = full
            }
        }

        if armed.altimeter {
            altimeter.startRelativeAltitudeUpdates(to: .main) { [weak self] data, _ in
                guard let self, let d = data else { return }
                var full = self.lastFull ?? FullMotionSample()
                full.relativeAltitudeM = d.relativeAltitude.doubleValue
                full.ts = Date()
                self.lastFull = full
            }
        }
    }

    public func stop() {
        motion.stopDeviceMotionUpdates()
        motion.stopAccelerometerUpdates()
        motion.stopGyroUpdates()
        motion.stopMagnetometerUpdates()
        if CMAltimeter.isRelativeAltitudeAvailable() {
            altimeter.stopRelativeAltitudeUpdates()
        }
        activePlan = MotionStreamPlan()
    }

    private func publish(_ full: FullMotionSample) {
        lastFull = full
        let vib = full.vibSample()
        last = vib
        onFullSample?(full)
        onSample?(vib)
    }
}
#endif
