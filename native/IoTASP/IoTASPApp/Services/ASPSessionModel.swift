import Combine
import Foundation
import SwiftUI

@MainActor
final class ASPSessionModel: ObservableObject {
    @Published var sink: FleetSink = .soundcore2A2DP
    @Published var motionArmed = false
    @Published var lastAbsA: Double = 0
    @Published var intenseVib = false
    @Published var alarm = AlarmStateMachine()

    private let detector = ImpulseDetector()
    #if canImport(CoreMotion)
    private var motion: PhoneMotionLogger?
    #endif
    private var ticker: AnyCancellable?

    func bootstrap() {
        try? ASPAudioSession.configureForFleetSink(sink)
        SensorKitGate.startReadersIfEntitled()
        arm()
        ticker = Timer.publish(every: 0.05, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] now in
                self?.alarm.tick(now: now, impulseEvent: nil, nightNY: Self.isNightNY())
                self?.objectWillChange.send()
            }
    }

    func arm() { alarm.arm(); objectWillChange.send() }
    func setHold(_ on: Bool) { alarm.setHoldManual(on); objectWillChange.send() }

    func simulateImpulse() {
        let e = ImpulseEvent(fromAccel: true, fromMicDiff: false, riseMs: 40)
        alarm.tick(now: Date(), impulseEvent: e, nightNY: Self.isNightNY())
        objectWillChange.send()
    }

    func applySink() {
        try? ASPAudioSession.configureForFleetSink(sink)
    }

    static func isNightNY() -> Bool {
        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = TimeZone(identifier: "America/New_York") ?? .current
        let hour = cal.component(.hour, from: Date())
        return hour >= 22 || hour < 7
    }
}
