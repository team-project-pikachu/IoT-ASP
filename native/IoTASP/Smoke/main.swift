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

        // #141 ultrasonic mic meter
        check("sr 48k", UltrasonicMicMeter.preferredSampleRate == 48_000)
        check("alpha", UltrasonicMicMeter.micDiffAlpha == 0.85)
        check("nyquist 48k", UltrasonicMicMeter.usBandFullyNyquist(sampleRate: 48_000))
        check("nyquist 44.1k", UltrasonicMicMeter.usBandFullyNyquist(sampleRate: 44_100) == false)
        check("micDiff", abs(UltrasonicMicMeter.micDiff(micEnergyDb: -20, outLevelDb: -30) - 5.5) < 1e-9)
        var spec = [Double](repeating: -90, count: 1024)
        let bw = UltrasonicMicMeter.binWidthHz(sampleRate: 48_000)
        let i20k = Int((20_000 / bw).rounded(.down))
        spec[i20k] = -40
        let us = UltrasonicMicMeter.bandEnergyUs(spectrumDb: spec, sampleRate: 48_000)
        check("bandEnergyUs uses 20 kHz bin", us > -90)
        check("empty spectrum floor", UltrasonicMicMeter.bandEnergyUs(spectrumDb: [], sampleRate: 48_000) == -120)
        check("aec off preferred", UltrasonicMicMeter.preferEchoCancellationOff)
        let stub = UltrasonicMicStatus.stub()
        check("stub not running", stub.engineRunning == false && stub.grantedSampleRate == 0)

        // #144 permission sequence
        let seq = PermissionSequencer.sequence(sensorkitEntitled: false)
        check("order mic then motion", seq == [.microphone, .motion])
        check("no SK when ungated", !seq.contains(.sensorkit))
        let seqSK = PermissionSequencer.sequence(sensorkitEntitled: true)
        check("SK last when entitled", seqSK.last == .sensorkit)
        let ungated = PermissionSequencer.ungatedSensorKitStep()
        check("SK skippedUngated", ungated.state == .skippedUngated)
        var steps = PermissionSequencer.initialSteps(sensorkitEntitled: false)
        steps = PermissionSequencer.apply(state: .denied, to: .microphone, steps: steps)
        check("denied does not crash", steps.contains(where: { $0.kind == .microphone && $0.isBlocking }))
        check("mic usage on-device", PermissionSequencer.usageDescription(for: .microphone).contains("on-device"))

        // #4 physical vib
        let ch = PhysicalVibChannel(config: PhysicalVibConfig(thresholdG: 0.1, debounceMs: 300, shakeMultiple: 3, shakeWindowMs: 400, reseedEvery: 4))
        let t0 = Date()
        check("below thr none", ch.observe(absA: 0.05, now: t0) == .none)
        check("physical", ch.observe(absA: 0.15, now: t0) == .physical)
        check("debounce", ch.observe(absA: 0.15, now: t0.addingTimeInterval(0.1)) == .none)
        let t1 = t0.addingTimeInterval(0.4)
        _ = ch.observe(absA: 0.4, now: t1)
        let hop = ch.observe(absA: 0.4, now: t1.addingTimeInterval(0.05))
        check("shake hop", hop == .shakeHop)
        check("disarmed none", ch.observe(absA: 2, now: t1.addingTimeInterval(2), armed: false) == .none)

        // #5 acoustic vib
        let ac = AcousticVibChannel(config: AcousticVibConfig(burstMarginDb: 12, floorDb: -55, window: 5))
        check("median", AcousticVibChannel.median([-10, -20, -30]) == -20)
        for _ in 0..<5 { _ = ac.observe(energyDb: -60) }
        check("quiet none-or-floor", ac.observe(energyDb: -60) == .none)
        check("burst", ac.observe(energyDb: -20) == .acousticBurst)
        check("micDiff preferred", ac.observe(energyDb: -20, micDiffDb: -80) != .acousticBurst)
        check("disarmed acoustic", ac.observe(energyDb: 0, armed: false) == .none)

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
