import SwiftUI
import WebKit

/// Desktop command center — the Vercel hop blaster, not a second control plane.
struct CommandCenterWebView: NSViewRepresentable {
    let url: URL

    func makeNSView(context: Context) -> WKWebView {
        let view = WKWebView()
        view.load(URLRequest(url: url))
        return view
    }

    func updateNSView(_ nsView: WKWebView, context: Context) {}
}
