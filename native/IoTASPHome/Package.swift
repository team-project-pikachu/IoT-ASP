// swift-tools-version: 5.9
import PackageDescription

/// M8 acoustic event-class model (#96). Builds without GoogleHomeSDK.
/// Full Home app wiring / Glass Shatter UI lands in #97.
let package = Package(
    name: "IoTASPHome",
    platforms: [.macOS(.v13), .iOS(.v16)],
    products: [
        .library(name: "HomeNestAlarm", targets: ["HomeNestAlarm"]),
    ],
    targets: [
        .target(
            name: "HomeNestAlarm",
            path: "Sources/HomeNestAlarm"
        ),
        .testTarget(
            name: "HomeNestAlarmTests",
            dependencies: ["HomeNestAlarm"],
            path: "Tests/HomeNestAlarmTests"
        ),
    ]
)
