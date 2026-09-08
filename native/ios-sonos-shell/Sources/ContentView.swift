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
        let osc = AVAudioSourceNode { _, _, frameCount, audioBufferList -> OSStatus in
            let abl = UnsafeMutableAudioBufferListPointer(audioBufferList)
            for buffer in abl {
                guard let data = buffer.mData?.assumingMemoryBound(to: Float.self) else { continue }
                let n = Int(frameCount)
                for i in 0..<n {
                    // Audible stub only — not the scientific ultrasonic band.
                    data[i] = 0.05 * sin(Float(i) * 2 * .pi * 880 / 48_000)
                }
            }
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
