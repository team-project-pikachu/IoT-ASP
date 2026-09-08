import Combine
import Foundation
import WatchConnectivity

@MainActor
final class WatchSessionModel: NSObject, ObservableObject, WCSessionDelegate {
    @Published var alarmState = AlarmState.armed.rawValue
    @Published var volBlast = false
    @Published var hold = false

    private let alarm = AlarmStateMachine()

    override init() {
        super.init()
        alarm.arm()
        if WCSession.isSupported() {
            let s = WCSession.default
            s.delegate = self
            s.activate()
        }
    }

    func sendImpulse() {
        let e = ImpulseEvent(fromAccel: true, fromMicDiff: false, riseMs: 30)
        alarm.tick(now: Date(), impulseEvent: e, nightNY: false)
        publish()
        mirrorToPhone()
    }

    func toggleHold() {
        hold.toggle()
        alarm.setHoldManual(hold)
        publish()
        mirrorToPhone()
    }

    private func publish() {
        alarmState = alarm.state.rawValue
        volBlast = alarm.volBlast
    }

    private func mirrorToPhone() {
        guard WCSession.isSupported(), WCSession.default.isReachable else { return }
        WCSession.default.sendMessage([
            "alarmState": alarm.state.rawValue,
            "impulse": alarm.impulse,
            "volBlast": alarm.volBlast,
            "holdManual": alarm.holdManual,
        ], replyHandler: nil, errorHandler: nil)
    }

    nonisolated func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {}
    #if os(iOS)
    nonisolated func sessionDidBecomeInactive(_ session: WCSession) {}
    nonisolated func sessionDidDeactivate(_ session: WCSession) { session.activate() }
    #endif
}
