import Foundation

/// Callback surface so M8 HomeNestAlarm / Glass Shatter (and #109 app shell) can ingest
/// SensorKit-or-stub vib without importing proprietary SDKs or depending on app targets.
public protocol SensorKitOnsetSink: AnyObject {
    func ingestSensorKitSample(_ sample: SensorKitSample)
}

/// Fan-out helper used by entitled readers or stub simulators.
public final class SensorKitProductHook: @unchecked Sendable {
    public weak var sink: SensorKitOnsetSink?

    public init(sink: SensorKitOnsetSink? = nil) {
        self.sink = sink
    }

    /// Emit a deterministic stub sample (CI / simulator). Never claims entitlement.
    public func emitStubPulse(ts: Date = Date()) {
        sink?.ingestSensorKitSample(.stubUnavailable(ts: ts))
    }

    /// Forward a live or stub sample to product pipelines.
    public func forward(_ sample: SensorKitSample) {
        sink?.ingestSensorKitSample(sample)
    }
}
