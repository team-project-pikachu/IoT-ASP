import SwiftUI

/// iPhone node — on/off + status. Command center is Vercel / the macOS wrapper.
struct ContentView: View {
    var body: some View {
        HopTabView()
            .preferredColorScheme(.dark)
    }
}
