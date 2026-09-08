import Foundation

#if canImport(AVFoundation)
import AVFoundation
#endif

/// Mic / energy sample for micDiff-style onset (aligns with web BURST_ONSET_DB ~9).
public struct MicEnergySample: Sendable, Equatable {
    public var energyDb: Double
    public var available: Bool
    public var permission: MicPermissionState
    public var source: String
    public var ts: Date

    public init(
        energyDb: Double = -80,
        available: Bool,
        permission: MicPermissionState,
        source: String,
        ts: Date = Date()
    ) {
        self.energyDb = energyDb
        self.available = available
        self.permission = permission
        self.source = source
        self.ts = ts
    }

    public static func unavailable(
        permission: MicPermissionState = .undetermined,
        reason: String = "mic_unavailable",
        ts: Date = Date()
    ) -> MicEnergySample {
        MicEnergySample(
            energyDb: -80,
            available: false,
            permission: permission,
            source: reason,
            ts: ts
        )
    }
}

public enum MicPermissionState: String, Sendable, Equatable {
    case undetermined
    case granted
    case denied
    case unavailable
}

public protocol MicEnergySink: AnyObject {
    func ingestMicEnergy(_ sample: MicEnergySample)
}

/// AVAudioSession + optional input-tap stub. Never crashes when mic APIs are missing (CI / Simulator).
public final class MicCaptureStub: @unchecked Sendable {
    public private(set) var last: MicEnergySample?
    public weak var sink: MicEnergySink?
    public var onSample: ((MicEnergySample) -> Void)?
    public private(set) var isRunning = false
    public private(set) var permission: MicPermissionState = .undetermined

    /// CI / unit-test path: skip real AVAudioEngine.
    public var stubOnly: Bool

    #if canImport(AVFoundation)
    private var engine: AVAudioEngine?
    #endif

    public init(stubOnly: Bool = true) {
        self.stubOnly = stubOnly
    }

    /// Privacy path: maps to `NSMicrophoneUsageDescription` on the app target.
    public func requestPermission(completion: @escaping (MicPermissionState) -> Void) {
        if stubOnly {
            permission = .granted
            completion(.granted)
            return
        }
        #if canImport(AVFoundation) && os(iOS)
        // iOS 16-safe path (avoid AVAudioApplication, which is newer).
        AVAudioSession.sharedInstance().requestRecordPermission { granted in
            let state: MicPermissionState = granted ? .granted : .denied
            self.permission = state
            completion(state)
        }
        #elseif canImport(AVFoundation)
        // macOS / non-iOS: real capture still gated by stubOnly + configureSession.
        permission = .undetermined
        completion(.undetermined)
        #else
        permission = .unavailable
        completion(.unavailable)
        #endif
    }

    /// Configure session for playback+record (fleet A2DP + micDiff). Safe no-op when stubOnly.
    public func configureSession() throws {
        #if canImport(AVFoundation)
        guard !stubOnly else { return }
        #if os(iOS)
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.playAndRecord, mode: .measurement, options: [.defaultToSpeaker, .allowBluetoothA2DP])
        try session.setActive(true)
        #endif
        #endif
    }

    public func start() {
        stop()
        isRunning = true
        if stubOnly || permission == .denied || permission == .unavailable {
            let sample = MicEnergySample.unavailable(permission: permission, reason: "mic_stub_idle")
            emit(sample)
            isRunning = false
            return
        }

        #if canImport(AVFoundation)
        do {
            try configureSession()
            let eng = AVAudioEngine()
            let input = eng.inputNode
            let format = input.outputFormat(forBus: 0)
            // Install a quiet tap; if hardware is absent, installTap may throw — catch and stub.
            input.installTap(onBus: 0, bufferSize: 1024, format: format) { [weak self] buffer, _ in
                guard let self, self.isRunning else { return }
                let db = Self.rmsDb(buffer: buffer)
                self.emit(MicEnergySample(
                    energyDb: db,
                    available: true,
                    permission: .granted,
                    source: "avaudioengine"
                ))
            }
            try eng.start()
            engine = eng
        } catch {
            emit(.unavailable(permission: permission, reason: "mic_start_failed"))
            isRunning = false
            engine = nil
        }
        #else
        emit(.unavailable(permission: .unavailable, reason: "avfoundation_not_linked"))
        isRunning = false
        #endif
    }

    public func stop() {
        isRunning = false
        #if canImport(AVFoundation)
        engine?.inputNode.removeTap(onBus: 0)
        engine?.stop()
        engine = nil
        #endif
    }

    /// Inject a micDiff-style energy reading for tests / Glass Shatter hooks.
    public func injectEnergyDb(_ energyDb: Double, ts: Date = Date()) {
        emit(MicEnergySample(
            energyDb: energyDb,
            available: true,
            permission: permission == .undetermined ? .granted : permission,
            source: "synthetic_mic",
            ts: ts
        ))
    }

    private func emit(_ sample: MicEnergySample) {
        last = sample
        onSample?(sample)
        sink?.ingestMicEnergy(sample)
    }

    #if canImport(AVFoundation)
    private static func rmsDb(buffer: AVAudioPCMBuffer) -> Double {
        guard let ch = buffer.floatChannelData?[0] else { return -80 }
        let n = Int(buffer.frameLength)
        guard n > 0 else { return -80 }
        var sum: Float = 0
        for i in 0..<n {
            let v = ch[i]
            sum += v * v
        }
        let rms = sqrt(sum / Float(n))
        let db = 20 * log10(max(rms, 1e-7))
        return Double(db)
    }
    #endif
}
