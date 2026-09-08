// swift-tools-version: 5.9
import PackageDescription

/// Google Home / Nest + Gemini acoustic-event MVP (M8) and SensorKit-ready app shell (M9).
/// Stub mode builds without proprietary GoogleHomeSDK (`#if canImport(GoogleHomeSDK)`).
///
/// Build: `swift build` from this directory, or `make home-ios-build` / `scripts/home_ios_build.sh` from repo root.
/// App entry for M9: `AppShellRootView` (M8 Nest/Glass tabs + SensorKit / Motion / Mic placeholders).
let package = Package(
    name: "IoTASPHome",
    platforms: [.macOS(.v13), .iOS(.v16)],
    products: [
        .library(name: "AppShell", targets: ["AppShell"]),
        .library(name: "HomeNestAlarm", targets: ["HomeNestAlarm"]),
        .library(name: "HomeNestAlarmUI", targets: ["HomeNestAlarmUI"]),
    ],
    targets: [
        .target(
            name: "AppShell",
            path: "Sources/AppShell"
        ),
        .target(
            name: "HomeNestAlarm",
            path: "Sources/HomeNestAlarm"
        ),
        .target(
            name: "HomeNestAlarmUI",
            dependencies: ["AppShell", "HomeNestAlarm"],
            path: "Sources/HomeNestAlarmUI"
        ),
        .testTarget(
            name: "HomeNestAlarmTests",
            dependencies: ["HomeNestAlarm", "AppShell"],
            path: "Tests/HomeNestAlarmTests"
        ),
    ]
)
