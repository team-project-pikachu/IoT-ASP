// swift-tools-version: 5.9
import PackageDescription

/// Shared alarm / impulse / fleet logic — `swift test` without full Xcode.app.
let package = Package(
    name: "IoTASPShared",
    platforms: [.macOS(.v13), .iOS(.v16), .watchOS(.v9)],
    products: [
        .library(name: "IoTASPShared", targets: ["IoTASPShared"]),
    ],
    targets: [
        .target(
            name: "IoTASPShared",
            path: "Shared",
            exclude: [
                "Audio/ASPAudioSession.swift",
                "Sensors/SensorKitGate.swift",
                "Sensors/PhoneMotionLogger.swift",
            ],
            sources: [
                "Alarm/AlarmStateMachine.swift",
                "Sensors/ImpulseDetector.swift",
                "Fleet/FleetConfig.swift",
            ]
        ),
        .testTarget(
            name: "IoTASPSharedTests",
            dependencies: ["IoTASPShared"],
            path: "Tests"
        ),
    ]
)
