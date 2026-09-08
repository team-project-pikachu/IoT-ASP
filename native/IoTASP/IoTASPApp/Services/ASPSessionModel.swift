import Combine
import Foundation
import SwiftUI

@MainActor
final class ASPSessionModel: ObservableObject {
    @Published var sink: FleetSink = .soundcore2A2DP {
        didSet { applySink() }
    }
    @Published var motionArmed = false {
        didSet { syncMotion() }
    }
    @Published var lastAbsA: Double = 0
    @Published var intenseVib = false
    @Published var sessionError: String?
    @Published var alarm = AlarmStateMachine()

    private let detector = ImpulseDetector()
    #if canImport(CoreMotion)
    private var motion: PhoneMotionLogger?
    #endif
    private var ticker: AnyCancellable?
    private var pendingImpulse: ImpulseEvent?

    func bootstrap() {
        applySink()
        SensorKitGate.startReadersIfEntitled()
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

    func setHold(_ on: Bool) {
        alarm.setHoldManual(on)
        objectWillChange.send()
    }

    func simulateImpulse() {
        pendingImpulse = ImpulseEvent(fromAccel: true, fromMicDiff: false, riseMs: 40)
    }

    func applySink() {
        do {
            try ASPAudioSession.configureForFleetSink(sink)
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
            logger.start(hz: 50)
            motion = logger
        } else {
            motion?.stop()
            motion = nil
        }
        #endif
    }

    private func ingest(_ sample: VibSample) {
        lastAbsA = sample.absA
        intenseVib = detector.intenseVibProxy(absA: sample.absA, lfEnergyProxy: sample.absA)
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
