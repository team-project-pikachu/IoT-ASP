// swift-tools-version: 5.9
import PackageDescription

/// Google Home / Nest + Gemini acoustic-event MVP (M8).
/// Stub mode builds without proprietary GoogleHomeSDK (`#if canImport(GoogleHomeSDK)`).
///
/// Build: `swift build` from this directory, or `make home-ios-build` / `scripts/home_ios_build.sh` from repo root.
let package = Package(
    name: "IoTASPHome",
    platforms: [.macOS(.v13), .iOS(.v16)],
    products: [
        .library(name: "HomeNestAlarm", targets: ["HomeNestAlarm"]),
        .library(name: "HomeNestAlarmUI", targets: ["HomeNestAlarmUI"]),
    ],
    targets: [
        .target(
            name: "HomeNestAlarm",
            path: "Sources/HomeNestAlarm"
        ),
        .target(
            name: "HomeNestAlarmUI",
            dependencies: ["HomeNestAlarm"],
            path: "Sources/HomeNestAlarmUI"
        ),
        .testTarget(
            name: "HomeNestAlarmTests",
            dependencies: ["HomeNestAlarm"],
            path: "Tests/HomeNestAlarmTests"
        ),
    ]
)
