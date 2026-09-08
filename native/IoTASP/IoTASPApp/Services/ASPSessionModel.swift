import Combine
import Foundation
import SwiftUI
#if canImport(AVFoundation)
import AVFoundation
#endif

@MainActor
final class ASPSessionModel: ObservableObject {
    @Published var sink: FleetSink = .soundcore2A2DP {
        didSet { applySink() }
    }
    @Published var motionArmed = false {
        didSet { syncMotion() }
    }
    @Published var micArmed = false {
        didSet {
            syncMic()
            applySink()
        }
    }
    @Published var micStatus = UltrasonicMicStatus.stub()
    @Published var lastAbsA: Double = 0
    @Published var lastAbsOmega: Double = 0
    @Published var motionAvailability = MotionAvailability.simulatorSafe
    @Published var motionPlanHz: Double = CoreMotionSuite.defaultHz
    @Published var intenseVib = false
    @Published var sessionError: String?
    @Published var permissionSteps: [PermissionStep] = PermissionSequencer.initialSteps(
        sensorkitEntitled: SensorKitGate.entitlementDeclared
    )
    @Published var alarm = AlarmStateMachine()

    private let detector = ImpulseDetector()
    private let physicalVib = PhysicalVibChannel()
    private let acousticVib = AcousticVibChannel()
    @Published var lastAcousticEvent: String = "none"
    @Published var materialPreset: MaterialPreset = .table {
        didSet { arming = VibArming.defaults(for: materialPreset) }
    }
    @Published var arming: VibArming = VibArming.defaults(for: .table)
    @Published var vibClass: String = "none"
    @Published var lfEnergyDb: Double = -120
    private let lfProxy = LfAccelProxy()
    @Published var lastPhysicalEvent: String = "none"
    @Published var shakeCount: Int = 0
    #if canImport(CoreMotion)
    private var motion: PhoneMotionLogger?
    #endif
    #if canImport(AVFoundation)
    private var mic: UltrasonicMicCapture?
    #endif
    private var ticker: AnyCancellable?
    private var pendingImpulse: ImpulseEvent?

    func bootstrap() {
        applySink()
        _ = SensorKitGate.startReadersIfEntitled()
        runPermissionSequence()
        arm()
        ticker = Timer.publish(every: 0.05, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] now in
                guard let self else { return }
                let event = self.pendingImpulse
                self.pendingImpulse = nil
                self.alarm.tick(now: now, impulseEvent: event, nightNY: Self.isNightNY())
                self.objectWillChange.send()
            }
    }

    func arm() {
        alarm.arm()
        objectWillChange.send()
    }

    /// First-run / re-arm: explain copy is already in `permissionSteps`; then mic → motion.
    /// Denied permissions do not crash — status stays denied and sensors stay unarmed.
    func runPermissionSequence() {
        permissionSteps = PermissionSequencer.initialSteps(
            sensorkitEntitled: SensorKitGate.entitlementDeclared
        )
        if !SensorKitGate.entitlementDeclared {
            permissionSteps.append(PermissionSequencer.ungatedSensorKitStep())
        }
        #if canImport(AVFoundation)
        let session = AVAudioSession.sharedInstance()
        switch session.recordPermission {
        case .granted:
            permissionSteps = PermissionSequencer.apply(state: .authorized, to: .microphone, steps: permissionSteps)
        case .denied:
            permissionSteps = PermissionSequencer.apply(state: .denied, to: .microphone, steps: permissionSteps)
            micArmed = false
        default:
            session.requestRecordPermission { [weak self] ok in
                Task { @MainActor in
                    self?.permissionSteps = PermissionSequencer.apply(
                        state: ok ? .authorized : .denied,
                        to: .microphone,
                        steps: self?.permissionSteps ?? []
                    )
                    if !ok { self?.micArmed = false }
                }
            }
        }
        #endif
        permissionSteps = PermissionSequencer.apply(
            state: motionArmed ? .authorized : .notDetermined,
            to: .motion,
            steps: permissionSteps
        )
        objectWillChange.send()
    }

    func setHold(_ on: Bool) {
        alarm.setHoldManual(on)
        objectWillChange.send()
    }

    func simulateImpulse() {
        pendingImpulse = ImpulseEvent(fromAccel: true, fromMicDiff: false, riseMs: 40)
    }

    func applySink() {
        do {
            try ASPAudioSession.configureForFleetSink(sink, micArmed: micArmed)
            sessionError = nil
        } catch {
            sessionError = error.localizedDescription
        }
    }

    private func syncMotion() {
        #if canImport(CoreMotion)
        if motionArmed {
            let logger = PhoneMotionLogger()
            logger.onSample = { [weak self] sample in
                self?.ingest(sample)
            }
            logger.start(hz: CoreMotionSuite.defaultHz)
            motionAvailability = logger.availability
            motionPlanHz = logger.activePlan.hz
            motion = logger
        } else {
            motion?.stop()
            motion = nil
        }
        #endif
    }

    private func syncMic() {
        #if canImport(AVFoundation)
        if micArmed {
            let cap = UltrasonicMicCapture()
            cap.onMeter = { [weak self] energy, diff in
                guard let self else { return }
                self.micStatus = cap.status
                let ev = self.acousticVib.observe(energyDb: energy, micDiffDb: diff, armed: self.arming.acoustic)
                self.lastAcousticEvent = ev.rawValue
                self.vibClass = VibChannelPolicy.classify(
                    physical: PhysicalVibEvent(rawValue: self.lastPhysicalEvent) ?? .none,
                    acoustic: ev,
                    arming: self.arming
                )
                if ev == .acousticBurst {
                    self.pendingImpulse = ImpulseEvent(fromAccel: false, fromMicDiff: true, riseMs: 40)
                }
            }
            cap.start()
            mic = cap
            micStatus = cap.status
        } else {
            mic?.stop()
            mic = nil
            micStatus.engineRunning = false
        }
        #endif
    }

    private func ingest(_ sample: VibSample) {
        lastAbsA = sample.absA
        lastAbsOmega = sample.absOmega
        intenseVib = detector.intenseVibProxy(absA: sample.absA, lfEnergyProxy: sample.absA)
        let phys = physicalVib.observe(absA: sample.absA, armed: arming.physical)
        lastPhysicalEvent = phys.rawValue
        shakeCount = physicalVib.shakeCount
        if let infra = lfProxy.observe(absA: sample.absA) {
            lfEnergyDb = lfProxy.lfEnergyDb
            if materialPreset == .chair, arming.physical, phys == .none {
                vibClass = infra
            }
        } else {
            lfEnergyDb = lfProxy.lfEnergyDb
        }
        if vibClass != "infra_felt" {
            vibClass = VibChannelPolicy.classify(
                physical: phys,
                acoustic: AcousticVibEvent(rawValue: lastAcousticEvent) ?? .none,
                arming: arming
            )
        }
        if phys == .shakeHop || phys == .shakeReseed {
            pendingImpulse = ImpulseEvent(fromAccel: true, fromMicDiff: false, riseMs: 40)
        }
        if let event = detector.observeAccel(sample) {
            pendingImpulse = event
        }
    }

    static func isNightNY() -> Bool {
        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = TimeZone(identifier: "America/New_York") ?? .current
        let hour = cal.component(.hour, from: Date())
        return hour >= 22 || hour < 7
    }
}
