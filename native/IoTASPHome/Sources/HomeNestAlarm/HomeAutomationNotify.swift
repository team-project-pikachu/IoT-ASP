import Foundation

/// Home Automation / Nest notification hook for glass-shatter (M8 / #97).
/// Live GoogleHomeSDK Automation API + Nest premium notify remain owner-gated (OAuth).
public protocol HomeAutomationNotifyClient: Sendable {
    /// Returns true when a notify was actually delivered (live path).
    /// Stub always returns false and records the TODO reason.
    func notifyGlassShatter(
        cameraId: String?,
        confidence: Double,
        escalateDb: Double
    ) async -> HomeNotifyAttempt
}

public struct HomeNotifyAttempt: Sendable, Equatable {
    public var delivered: Bool
    public var pending: Bool
    public var todoReason: String

    public init(delivered: Bool, pending: Bool, todoReason: String) {
        self.delivered = delivered
        self.pending = pending
        self.todoReason = todoReason
    }
}

/// Default stub: surfaces Automation/notify as an explicit pending TODO (no network).
public struct TodoHomeAutomationNotifyClient: HomeAutomationNotifyClient {
    public static let todoMessage =
        "TODO(M8/#97): Wire Home Automation / Nest notification for glass_shatter (owner OAuth + Nest premium)."

    public init() {}

    public func notifyGlassShatter(
        cameraId: String?,
        confidence: Double,
        escalateDb: Double
    ) async -> HomeNotifyAttempt {
        _ = cameraId
        _ = confidence
        _ = escalateDb
        return HomeNotifyAttempt(
            delivered: false,
            pending: true,
            todoReason: Self.todoMessage
        )
    }
}
