import Foundation

/// Nest / Home Device API camera trait sketch (stub).
/// Real traits come from Home APIs Device guide once SDK + Nest premium account are linked.
public struct NestCameraDevice: Identifiable, Sendable, Codable {
    public var id: String
    public var displayName: String
    public var supportsAudio: Bool
    public var supportsSnapshot: Bool

    public init(id: String, displayName: String, supportsAudio: Bool = true, supportsSnapshot: Bool = true) {
        self.id = id
        self.displayName = displayName
        self.supportsAudio = supportsAudio
        self.supportsSnapshot = supportsSnapshot
    }
}

public struct CameraSnapshotContext: Sendable, Codable {
    public var cameraId: String
    public var eventClass: AcousticEventClass
    public var note: String
    public var ts: Date

    public init(cameraId: String, eventClass: AcousticEventClass, note: String = "stub-snapshot", ts: Date = Date()) {
        self.cameraId = cameraId
        self.eventClass = eventClass
        self.note = note
        self.ts = ts
    }
}

public struct NestCameraCatalog: Sendable {
    public var devices: [NestCameraDevice]

    public init(devices: [NestCameraDevice] = [
        NestCameraDevice(id: "nest-cam-stub-1", displayName: "Stub Nest Cam (indoor)"),
    ]) {
        self.devices = devices
    }

    public func snapshotContext(for event: AcousticEventClass) -> CameraSnapshotContext? {
        guard let cam = devices.first(where: { $0.supportsSnapshot }) else { return nil }
        return CameraSnapshotContext(cameraId: cam.id, eventClass: event)
    }
}
