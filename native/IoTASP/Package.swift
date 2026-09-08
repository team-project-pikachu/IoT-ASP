// swift-tools-version: 5.9
import PackageDescription

/// Shared alarm / impulse / fleet / CoreMotion-suite logic — `swift run IoTASPSmoke` without Xcode.app.
let package = Package(
    name: "IoTASPShared",
    platforms: [.macOS(.v13), .iOS(.v16), .watchOS(.v9)],
    products: [
        .library(name: "IoTASPShared", targets: ["IoTASPShared"]),
        .executable(name: "IoTASPSmoke", targets: ["IoTASPSmoke"]),
    ],
    targets: [
        .target(
            name: "IoTASPShared",
            path: "Shared",
            exclude: [
                // iOS-only (CoreMotion / AVFoundation / SensorKit). CLT macOS cannot link them.
                "Audio/ASPAudioSession.swift",
                "Audio/UltrasonicMicCapture.swift",
                "Sensors/SensorKitGate.swift",
                "Sensors/PhoneMotionLogger.swift",
            ]
        ),
        .executableTarget(
            name: "IoTASPSmoke",
            dependencies: ["IoTASPShared"],
            path: "Smoke"
        ),
        // XCTest requires full Xcode.app. On CLT-only hosts run:
        //   swift run IoTASPSmoke
        //   swift Scripts/alarm_smoke.swift
    ]
)
