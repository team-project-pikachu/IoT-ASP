import AVFoundation
import SwiftUI

/// Placeholder hop tone + system AirPlay / route picker for Sonos Beam (Node 3).
struct ContentView: View {
    @State private var engine: AVAudioEngine?
    @State private var playing = false

    var body: some View {
        VStack(spacing: 24) {
            Text("IoT-ASP Sonos shell")
                .font(.title2)
            Text("Node 3 — AirPlay to Beam Gen 2. Not A2DP Soundcore parity.")
                .font(.footnote)
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)

            RoutePicker()
                .frame(width: 44, height: 44)

            Button(playing ? "Stop tone" : "Play stub tone") {
                toggleTone()
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
    }

    private func toggleTone() {
        if playing {
            engine?.stop()
            engine = nil
            playing = false
            return
        }
        let eng = AVAudioEngine()
        // Preserve phase across render callbacks; derive increment from engine output rate
        // (AirPlay routes are often not 48 kHz).
        let phaseBox = TonePhaseBox()
        let sampleRate = eng.outputNode.outputFormat(forBus: 0).sampleRate
        let hz = sampleRate > 0 ? sampleRate : 48_000
        let phaseInc = Float(2 * Double.pi * 880 / hz)
        let twoPi = Float(2 * Double.pi)
        let osc = AVAudioSourceNode { _, _, frameCount, audioBufferList -> OSStatus in
            let abl = UnsafeMutableAudioBufferListPointer(audioBufferList)
            var phase = phaseBox.phase
            for buffer in abl {
                guard let data = buffer.mData?.assumingMemoryBound(to: Float.self) else { continue }
                let n = Int(frameCount)
                for i in 0..<n {
                    // Audible stub only — not the scientific ultrasonic band.
                    data[i] = 0.05 * sin(phase)
                    phase += phaseInc
                    if phase >= twoPi { phase -= twoPi }
                }
            }
            phaseBox.phase = phase
            return noErr
        }
        eng.attach(osc)
        eng.connect(osc, to: eng.mainMixerNode, format: nil)
        do {
            try eng.start()
            engine = eng
            playing = true
        } catch {
            print("engine start failed: \(error)")
        }
    }
}

/// Mutable phase carrier so the render callback can close over a reference type.
private final class TonePhaseBox {
    var phase: Float = 0
}
