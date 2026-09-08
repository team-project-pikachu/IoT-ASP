#!/usr/bin/env swift
import Foundation

// Smoke assertions for AlarmStateMachine without XCTest (CLT-only hosts).
// Run from native/IoTASP: swift Scripts/alarm_smoke.swift  (after copying sources inline)

// Minimal inline copy of critical logic to avoid module link without Xcode:
enum AlarmState: String { case armed, triggered, sustaining, cleared }
final class M {
    var state: AlarmState = .cleared
    var volBlast = false
    var hold = false
    var quiet: Date?
    func arm() { if !hold { state = .armed } }
    func holdOn() { hold = true; state = .cleared; volBlast = false }
    func tick(impulse: Bool, now: Date) {
        if hold { return }
        if impulse {
            quiet = nil
            state = (state == .armed || state == .cleared) ? .triggered : .sustaining
            volBlast = true
            return
        }
        guard state == .triggered || state == .sustaining else { return }
        if quiet == nil { quiet = now }
        if now.timeIntervalSince(quiet!) >= 2.5 {
            state = .armed
            volBlast = false
            quiet = nil
        } else {
            state = .sustaining
            volBlast = true
        }
    }
}

func assert(_ cond: Bool, _ msg: String) {
    if !cond { fputs("FAIL: \(msg)\n", stderr); exit(1) }
}

let m = M()
m.arm()
assert(m.state == .armed, "arm")
let t0 = Date()
m.tick(impulse: true, now: t0)
assert(m.state == .triggered && m.volBlast, "trigger blast")
m.tick(impulse: false, now: t0.addingTimeInterval(0.5))
assert(m.state == .sustaining, "sustain")
m.tick(impulse: false, now: t0.addingTimeInterval(3.0))
assert(m.state == .armed && !m.volBlast, "clear re-arm")
m.holdOn()
m.tick(impulse: true, now: Date())
assert(m.state == .cleared && !m.volBlast, "hold wins")
print("alarm_smoke OK")
