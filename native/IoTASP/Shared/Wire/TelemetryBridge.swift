import Foundation

/// schemaVersion 1 telemetry/patch bridge (#147). Empty telemetry URL disables POST (web parity).
/// Never embeds Gemini/Vertex keys.
public struct NativeTelemetry: Codable, Equatable {
    public var schemaVersion: Int
    public var deviceId: String
    public var ts: String
    public var algo: String
    public var suddenFreq: Bool
    public var absA: Double?
    public var ax: Double?
    public var ay: Double?
    public var az: Double?
    public var gx: Double?
    public var gy: Double?
    public var gz: Double?
    public var absOmega: Double?
    public var micEnergy: Double?
    public var micDiff: Double?
    public var bandEnergyUs: Double?
    public var band: String
    public var power: String
    public var vibClass: String?
    public var materialPreset: String?
    public var holdManual: Bool
    public var lfDriveCapable: Bool
    public var alarmState: String?
    public var impulse: Bool?

    public init(
        schemaVersion: Int = 1,
        deviceId: String,
        ts: String,
        algo: String = "hop",
        suddenFreq: Bool = false,
        absA: Double? = nil,
        ax: Double? = nil,
        ay: Double? = nil,
        az: Double? = nil,
        gx: Double? = nil,
        gy: Double? = nil,
        gz: Double? = nil,
        absOmega: Double? = nil,
        micEnergy: Double? = nil,
        micDiff: Double? = nil,
        bandEnergyUs: Double? = nil,
        band: String = "17-23k",
        power: String = "ac120",
        vibClass: String? = nil,
        materialPreset: String? = nil,
        holdManual: Bool = false,
        lfDriveCapable: Bool = false,
        alarmState: String? = nil,
        impulse: Bool? = nil
    ) {
        self.schemaVersion = schemaVersion
        self.deviceId = deviceId
        self.ts = ts
        self.algo = algo
        self.suddenFreq = suddenFreq
        self.absA = absA
        self.ax = ax
        self.ay = ay
        self.az = az
        self.gx = gx
        self.gy = gy
        self.gz = gz
        self.absOmega = absOmega
        self.micEnergy = micEnergy
        self.micDiff = micDiff
        self.bandEnergyUs = bandEnergyUs
        self.band = band
        self.power = power
        self.vibClass = vibClass
        self.materialPreset = materialPreset
        self.holdManual = holdManual
        self.lfDriveCapable = lfDriveCapable
        self.alarmState = alarmState
        self.impulse = impulse
    }
}

public struct NativePatch: Codable, Equatable {
    public var schemaVersion: Int?
    public var algo: String
    public var fMin: Double?
    public var fMax: Double?
    public var vol: Double?
    public var holdManual: Bool?

    public init(schemaVersion: Int? = 1, algo: String, fMin: Double? = nil, fMax: Double? = nil, vol: Double? = nil, holdManual: Bool? = nil) {
        self.schemaVersion = schemaVersion
        self.algo = algo
        self.fMin = fMin
        self.fMax = fMax
        self.vol = vol
        self.holdManual = holdManual
    }
}

public enum TelemetryBridge {
    public static let schemaVersion = 1
    public static let allowedAlgos: Set<String> = [
        "hop", "am_gate", "shriek_chirp", "shriek_sweep", "burst", "infra_mod",
        "cry_mirror", "siren_mirror", "death_metal_mirror",
    ]

    public static func shouldPost(telemetryURL: String) -> Bool {
        !telemetryURL.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    public static func encode(_ t: NativeTelemetry) throws -> Data {
        let enc = JSONEncoder()
        enc.outputFormatting = [.sortedKeys]
        return try enc.encode(t)
    }

    public static func requiredOK(_ t: NativeTelemetry) -> Bool {
        t.schemaVersion == schemaVersion && !t.deviceId.isEmpty && !t.ts.isEmpty && allowedAlgos.contains(t.algo)
    }

    /// Hold / Manual: refuse applying remote patches.
    public static func applyPatch(data: Data, holdManual: Bool) throws -> NativePatch? {
        if holdManual { return nil }
        let patch = try JSONDecoder().decode(NativePatch.self, from: data)
        guard allowedAlgos.contains(patch.algo) else { return nil }
        return patch
    }

    public static func fromSession(
        deviceId: String,
        sample: FullMotionSample?,
        mic: UltrasonicMicStatus,
        vibClass: String,
        material: MaterialPreset,
        alarm: AlarmStateMachine,
        hold: Bool
    ) -> NativeTelemetry {
        let iso = ISO8601DateFormatter()
        iso.formatOptions = [.withInternetDateTime]
        return NativeTelemetry(
            deviceId: deviceId,
            ts: iso.string(from: Date()),
            algo: "hop",
            suddenFreq: false,
            absA: sample?.absA,
            ax: sample?.ax,
            ay: sample?.ay,
            az: sample?.az,
            gx: sample?.gx,
            gy: sample?.gy,
            gz: sample?.gz,
            absOmega: sample?.absOmega,
            micEnergy: mic.lastBandEnergyUs,
            micDiff: mic.lastMicDiff,
            bandEnergyUs: mic.lastBandEnergyUs,
            vibClass: vibClass,
            materialPreset: material.rawValue,
            holdManual: hold,
            alarmState: alarm.state.rawValue,
            impulse: alarm.impulse
        )
    }
}
