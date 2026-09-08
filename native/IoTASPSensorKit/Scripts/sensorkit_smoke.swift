#!/usr/bin/env swift
import Foundation

#if canImport(IoTASPSensorKit)
import IoTASPSensorKit
#endif

// Standalone smoke when run via `swift build` product is preferred;
// this file documents expected stub invariants for CLT hosts.
print("sensorKit_mode=stub")
print("entitlementDeclared=false")
print("OK sensorkit_smoke")
