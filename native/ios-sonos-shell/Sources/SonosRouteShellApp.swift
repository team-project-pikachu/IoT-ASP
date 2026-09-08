import AVFoundation
import SwiftUI

@main
struct SonosRouteShellApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .onAppear {
                    SonosAudioSession.configureForAirPlay()
                }
        }
    }
}

enum SonosAudioSession {
    /// Long-form playback so the system AirPlay route list includes speakers.
    /// Cite: https://developer.apple.com/documentation/avfoundation/supporting-airplay-in-your-app
    static func configureForAirPlay() {
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playback, mode: .default, policy: .longFormAudio)
            try session.setActive(true)
        } catch {
            // Stub: surface in UI when this graduates past research.
            print("AVAudioSession configure failed: \(error)")
        }
    }
}
