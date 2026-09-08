import SwiftUI

struct WatchContentView: View {
    @EnvironmentObject var model: WatchSessionModel

    var body: some View {
        VStack(spacing: 12) {
            Text(model.operatorStatus)
                .font(.title2)
            Toggle("Hold / Manual", isOn: Binding(
                get: { model.hold },
                set: { _ in model.toggleHold() }
            ))
        }
        .padding()
    }
}
