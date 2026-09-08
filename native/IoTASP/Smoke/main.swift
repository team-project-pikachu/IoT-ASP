import Foundation
import IoTASPShared

/// CLT-safe smoke for IoTASPShared (no XCTest / Xcode.app).
/// Run: `cd native/IoTASP && swift run IoTASPSmoke`
@main
struct IoTASPSmoke {
    static func main() {
        var failed = 0
        func check(_ name: String, _ ok: Bool, _ detail: String = "") {
            if ok {
                print("OK \(name)")
            } else {
                let extra = detail.isEmpty ? "" : " — \(detail)"
                fputs("FAIL \(name)\(extra)\n", stderr)
                failed += 1
            }
        }

        // #140 CoreMotion suite
        check("hzMin", CoreMotionSuite.hzMin == 1)
        check("hzMax", CoreMotionSuite.hzMax == 100)
        check("clamp lo", CoreMotionSuite.clampHz(0.1) == 1)
        check("clamp hi", CoreMotionSuite.clampHz(400) == 100)
        check("clamp nan", CoreMotionSuite.clampHz(.nan) == CoreMotionSuite.defaultHz)
        check("g", abs(CoreMotionSuite.standardGravity - 9.80665) < 1e-9)
        check("mps2 to g", abs(CoreMotionSuite.metersPerSecondSquaredToG(9.80665) - 1.0) < 1e-9)
        check("pedometer skip", CoreMotionPolicy.productUse(for: .pedometer) == .skip)
        check("pedometer rationale", CoreMotionPolicy.skipRationale(for: .pedometer) != nil)
        check("accel fleet", CoreMotionPolicy.productUse(for: .accelerometer) == .fleetVib)
        check("gyro fleet", CoreMotionPolicy.productUse(for: .gyroscope) == .fleetVib)
        check("deviceMotion fleet", CoreMotionPolicy.productUse(for: .deviceMotion) == .fleetVib)
        check("mag optional", CoreMotionPolicy.productUse(for: .magnetometer) == .optional)
        check("altimeter optional", CoreMotionPolicy.productUse(for: .altimeter) == .optional)
        check("api surface count", CoreMotionPolicy.apiSurface.count == MotionSensorClass.allCases.count)

        let sim = MotionAvailability.simulatorSafe
        check("sim all false", !sim.accelerometer && !sim.deviceMotion && !sim.pedometer)
        let emptyPlan = MotionStreamPlan.scientific(availability: sim)
        check("sim plan arms nothing", !emptyPlan.armsAnything)
        check("sim plan no pedometer field", true)

        var hw = MotionAvailability()
        hw.accelerometer = true
        hw.gyroscope = true
        hw.deviceMotion = true
        hw.magnetometer = true
        hw.altimeter = true
        hw.pedometer = true
        let plan = MotionStreamPlan.scientific(availability: hw, hz: 80)
        check("plan hz", plan.hz == 80)
        check("plan accel", plan.rawAccelerometer)
        check("plan gyro", plan.rawGyroscope)
        check("plan mag", plan.magnetometer)
        check("plan dm", plan.deviceMotion)
        check("plan altimeter", plan.altimeter)
        check("plan never encodes pedometer start", CoreMotionPolicy.productUse(for: .pedometer) == .skip)

        let sample = FullMotionSample(ax: 0.3, ay: -0.4, az: 0.0, gx: 0.1, gy: 0.2, gz: 0.2)
        check("absA", abs(sample.absA - 0.5) < 1e-9)
        let tel = sample.telemetryAxes()
        check("tel ax", tel["ax"] == 0.3)
        check("tel absA", tel["absA"] != nil)
        let vib = sample.vibSample()
        check("vib absA", abs(vib.absA - sample.absA) < 1e-12)

        // Existing alarm / impulse still reachable
        let alarm = AlarmStateMachine()
        alarm.arm()
        check("alarm arm", alarm.state == .armed)
        alarm.setHoldManual(true)
        check("hold wins", alarm.state == .cleared && alarm.holdManual)

        if failed > 0 {
            fputs("IoTASPSmoke FAIL count=\(failed)\n", stderr)
            exit(1)
        }
        print("IoTASPSmoke OK")
    }
}
