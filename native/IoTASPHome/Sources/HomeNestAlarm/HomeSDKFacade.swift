import Foundation

/// Facade over Google Home APIs iOS SDK.
/// Get-started flow (docs summary): Sample → Get SDK → OAuth → Initialize home → Device/Camera/Automation.
/// Proprietary SDK is NOT vendored; stub builds use this facade when `GoogleHomeSDK` is absent.
public protocol HomeStructureClient: Sendable {
    var isAuthorized: Bool { get }
    func initializeHome() async throws
    func listCameraDeviceIds() async throws -> [String]
}

#if canImport(GoogleHomeSDK)
// TODO(M8): Wire real GoogleHomeSDK types once SPM/CocoaPods + OAuth (betty@bearresearch.io) are configured.
// See https://developers.home.google.com/apis/ios/get-started
public struct LiveHomeStructureClient: HomeStructureClient {
    public var isAuthorized: Bool = false
    public init() {}
    public func initializeHome() async throws {
        // TODO: Home.initialize / structure subscribe per Home APIs iOS guide
        throw HomeSDKError.notConfigured("Live GoogleHomeSDK path requires owner OAuth client")
    }
    public func listCameraDeviceIds() async throws -> [String] {
        throw HomeSDKError.notConfigured("Camera Device API traits require live SDK + Nest devices")
    }
}
#endif

public enum HomeSDKError: Error, Sendable, Equatable {
    case notConfigured(String)
    case unauthorized
}

/// Default stub used by CI / `swift build` without GoogleHomeSDK.
public struct StubHomeStructureClient: HomeStructureClient {
    public private(set) var isAuthorized: Bool
    public var stubCameraIds: [String]

    public init(isAuthorized: Bool = false, stubCameraIds: [String] = ["nest-cam-stub-1"]) {
        self.isAuthorized = isAuthorized
        self.stubCameraIds = stubCameraIds
    }

    public func initializeHome() async throws {
        // Owner must complete Google Home Developer Console + OAuth as betty@bearresearch.io.
        guard isAuthorized else { throw HomeSDKError.unauthorized }
    }

    public func listCameraDeviceIds() async throws -> [String] {
        guard isAuthorized else { throw HomeSDKError.unauthorized }
        return stubCameraIds
    }

    public mutating func markAuthorizedForTests() {
        isAuthorized = true
    }
}

/// Factory — prefers live SDK only when importable; otherwise stub.
public enum HomeStructureClientFactory {
    public static func makeDefault() -> any HomeStructureClient {
        #if canImport(GoogleHomeSDK)
        return LiveHomeStructureClient()
        #else
        return StubHomeStructureClient()
        #endif
    }
}
