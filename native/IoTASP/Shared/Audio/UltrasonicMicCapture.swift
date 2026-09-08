import AVFoundation
import Foundation

/// AVAudioEngine tap for hop-ultrasonic capture (#141).
/// Prefer 48 kHz; request AEC/NS/AGC off via `.measurement` (not voice-processing I/O).
/// Simulator / missing mic: `status` stays stub — no crash.
public final class UltrasonicMicCapture: @unchecked Sendable {
    private let engine = AVAudioEngine()
    public private(set) var status = UltrasonicMicStatus.stub()
    public var onMeter: ((Double, Double?) -> Void)?

    public init() {}

    public func start() {
        do {
            let session = AVAudioSession.sharedInstance()
            // playAndRecord + measurement: scientific capture; do not use .voiceChat (AEC on).
            try session.setCategory(
                .playAndRecord,
                mode: .measurement,
                options: [.allowBluetoothA2DP, .defaultToSpeaker, .mixWithOthers]
            )
            try session.setPreferredSampleRate(UltrasonicMicMeter.preferredSampleRate)
            try session.setPreferredInputNumberOfChannels(UltrasonicMicMeter.monoChannels)
            try session.setActive(true)

            let granted = session.sampleRate
            let input = engine.inputNode
            let format = input.outputFormat(forBus: 0)
            let fft = UltrasonicMicMeter.fftSize
            input.removeTap(onBus: 0)
            input.installTap(onBus: 0, bufferSize: AVAudioFrameCount(fft), format: format) { [weak self] buffer, _ in
                self?.ingest(buffer: buffer, sampleRate: format.sampleRate)
            }
            try engine.start()
            status = UltrasonicMicStatus(
                grantedSampleRate: granted,
                usBandOk: UltrasonicMicMeter.usBandFullyNyquist(sampleRate: granted),
                engineRunning: true,
                note: Self.honestyNote(granted: granted)
            )
        } catch {
            status = UltrasonicMicStatus.stub()
            status.note = "mic start failed: \(error.localizedDescription)"
            stop()
        }
    }

    public func stop() {
        engine.inputNode.removeTap(onBus: 0)
        engine.stop()
        var s = status
        s.engineRunning = false
        status = s
    }

    public static func honestyNote(granted: Double) -> String {
        let nyq = UltrasonicMicMeter.nyquist(sampleRate: granted)
        var parts = [
            "preferred 48000 Hz; granted \(Int(granted)) Hz; Nyquist \(Int(nyq)) Hz",
            "AEC/NS/AGC off requested via AVAudioSessionModeMeasurement (OS may override)",
        ]
        if !UltrasonicMicMeter.usBandFullyNyquist(sampleRate: granted) {
            parts.append("US band top 23 kHz not fully sampled — do not claim calibrated 17–23 kHz")
        }
        return parts.joined(separator: "; ")
    }

    private func ingest(buffer: AVAudioPCMBuffer, sampleRate: Double) {
        // Magnitude proxy (not a calibrated FFT): RMS dBFS of the tap.
        // Band-limited US energy needs an FFT; CLT/tests cover UltrasonicMicMeter.bandEnergyUs.
        guard let ch = buffer.floatChannelData?[0] else { return }
        let n = Int(buffer.frameLength)
        guard n > 0 else { return }
        var acc = 0.0
        for i in 0..<n {
            let x = Double(ch[i])
            acc += x * x
        }
        let rms = (acc / Double(n)).squareRoot()
        let db = rms > 1e-12 ? 20.0 * log10(rms) : -120
        var s = status
        s.lastBandEnergyUs = db
        s.grantedSampleRate = sampleRate
        s.usBandOk = UltrasonicMicMeter.usBandFullyNyquist(sampleRate: sampleRate)
        status = s
        onMeter?(db, s.lastMicDiff)
    }
}
