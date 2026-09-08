#!/usr/bin/env swift
import Foundation
#if canImport(HomeNestAlarm)
import HomeNestAlarm
#endif

// Standalone smoke when run via `swift build` artifacts is preferred.
// This file documents the expected CLI smoke path used by scripts/home_ios_build.sh:
//   cd native/IoTASPHome && swift build
print("home_nest_smoke: prefer `swift build` in native/IoTASPHome (see Scripts/README)")
