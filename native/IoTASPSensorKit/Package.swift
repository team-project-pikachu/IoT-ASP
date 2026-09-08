// swift-tools-version: 5.9
import PackageDescription

/// SensorKit entitlement-gated stub (M9 / #110).
/// Default (CI / CLT) builds **without** Apple SensorKit entitlement approval.
/// Entitled path is compile-gated via `-DASP_SENSORKIT_ENTITLED` + real entitlement —
/// never invent approvals or secrets in git.
///
/// Build: `swift build` here, or `make sensorkit-stub-build` / `scripts/sensorkit_stub_build.sh` from repo root.
let package = Package(
    name: "IoTASPSensorKit",
    platforms: [.macOS(.v13), .iOS(.v16)],
    products: [
        .library(name: "IoTASPSensorKit", targets: ["IoTASPSensorKit"]),
    ],
    targets: [
        .target(
            name: "IoTASPSensorKit",
            path: "Sources/IoTASPSensorKit"
        ),
        .testTarget(
            name: "IoTASPSensorKitTests",
            dependencies: ["IoTASPSensorKit"],
            path: "Tests/IoTASPSensorKitTests"
        ),
    ]
)
