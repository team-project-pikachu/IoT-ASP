// swift-tools-version: 5.9
import PackageDescription

/// CoreMotion + AVFoundation (mic) stubs for ultrasonic / hop (M9 / #111).
/// Feature-flagged / simulator-safe: builds on macOS CLT without device sensors.
/// Hooks feed HomeNestAlarm / Glass Shatter style onset callbacks without GoogleHomeSDK.
///
/// Build: `swift build` here, or `make motion-audio-build` / `scripts/motion_audio_build.sh`.
let package = Package(
    name: "IoTASPMotionAudio",
    platforms: [.macOS(.v13), .iOS(.v16)],
    products: [
        .library(name: "IoTASPMotionAudio", targets: ["IoTASPMotionAudio"]),
    ],
    targets: [
        .target(
            name: "IoTASPMotionAudio",
            path: "Sources/IoTASPMotionAudio"
        ),
        .testTarget(
            name: "IoTASPMotionAudioTests",
            dependencies: ["IoTASPMotionAudio"],
            path: "Tests/IoTASPMotionAudioTests"
        ),
    ]
)
