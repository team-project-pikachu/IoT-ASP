import AVKit
import SwiftUI

/// System AirPlay / audio route picker (AVKit).
/// Cite: https://developer.apple.com/documentation/avkit/avroutepickerview
struct RoutePicker: UIViewRepresentable {
    func makeUIView(context: Context) -> AVRoutePickerView {
        let view = AVRoutePickerView()
        view.prioritizesVideoDevices = false
        return view
    }

    func updateUIView(_ uiView: AVRoutePickerView, context: Context) {}
}
