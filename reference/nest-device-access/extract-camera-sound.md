# Extract: camera-sound

Source: https://developers.google.com/nest/device-access/traits/device/camera-sound

---

[Skip to main content](https://developers.google.com/nest/device-access/traits/device/camera-sound#main-content)

[![Device Access](https://www.gstatic.com/images/branding/googleg_gradient/1x/googleg_gradient_standard_64dp.png)](https://developers.google.com/nest/device-access)

- [Device Access](https://developers.google.com/nest/device-access)

[Guides](https://developers.google.com/nest/device-access/registration)[Traits](https://developers.google.com/nest/device-access/traits)[Reference](https://developers.google.com/nest/device-access/reference/rest)[Support](https://developers.google.com/nest/device-access/support)

`/`

- English
- Deutsch
- Español
- Español – América Latina
- Français
- Indonesia
- Italiano
- Polski
- Português – Brasil
- Tiếng Việt
- Türkçe
- Русский
- עברית
- العربيّة
- فارسی
- हिंदी
- বাংলা
- ภาษาไทย
- 中文 – 简体
- 中文 – 繁體
- 日本語
- 한국어

Sign in

- [Traits](https://developers.google.com/nest/device-access/traits)

[![Device Access](https://www.gstatic.com/images/branding/googleg_gradient/1x/googleg_gradient_standard_64dp.png)](https://developers.google.com/nest/device-access)

- [Device Access](https://developers.google.com/nest/device-access)

- [Guides](https://developers.google.com/nest/device-access/registration)
- [Traits](https://developers.google.com/nest/device-access/traits)
- [Reference](https://developers.google.com/nest/device-access/reference/rest)
- [Support](https://developers.google.com/nest/device-access/support)

- Traits

- [Overview](https://developers.google.com/nest/device-access/traits)
- Structure Traits



  - [Info](https://developers.google.com/nest/device-access/traits/structure/info)
  - [RoomInfo](https://developers.google.com/nest/device-access/traits/structure/room-info)

- Device Traits



  - [Connectivity](https://developers.google.com/nest/device-access/traits/device/connectivity)
  - [Fan](https://developers.google.com/nest/device-access/traits/device/fan)
  - [Humidity](https://developers.google.com/nest/device-access/traits/device/humidity)
  - [Info](https://developers.google.com/nest/device-access/traits/device/info)
  - [Settings](https://developers.google.com/nest/device-access/traits/device/settings)
  - [Temperature](https://developers.google.com/nest/device-access/traits/device/temperature)

- Thermostat Traits



  - [ThermostatEco](https://developers.google.com/nest/device-access/traits/device/thermostat-eco)
  - [ThermostatHvac](https://developers.google.com/nest/device-access/traits/device/thermostat-hvac)
  - [ThermostatMode](https://developers.google.com/nest/device-access/traits/device/thermostat-mode)
  - [ThermostatTemperatureSetpoint](https://developers.google.com/nest/device-access/traits/device/thermostat-temperature-setpoint)

- Camera Traits



  - [CameraClipPreview](https://developers.google.com/nest/device-access/traits/device/camera-clip-preview)
  - [CameraEventImage](https://developers.google.com/nest/device-access/traits/device/camera-event-image)
  - [CameraImage](https://developers.google.com/nest/device-access/traits/device/camera-image)
  - [CameraLiveStream](https://developers.google.com/nest/device-access/traits/device/camera-live-stream)
  - [CameraMotion](https://developers.google.com/nest/device-access/traits/device/camera-motion)
  - [CameraPerson](https://developers.google.com/nest/device-access/traits/device/camera-person)
  - [CameraSound](https://developers.google.com/nest/device-access/traits/device/camera-sound)

- Doorbell Traits



  - [DoorbellChime](https://developers.google.com/nest/device-access/traits/device/doorbell-chime)

- [Home](https://developers.google.com/)
- [Products](https://developers.google.com/products)
- [Device Access](https://developers.google.com/nest/device-access)
- [Traits](https://developers.google.com/nest/device-access/traits)


 Stay organized with collections


 Save and categorize content based on your preferences.


# CameraSound Schema

[Nest Cam (legacy)](https://developers.google.com/nest/device-access/api/camera)[Nest Hub Max](https://developers.google.com/nest/device-access/api/display)[Nest Doorbell (legacy)](https://developers.google.com/nest/device-access/api/doorbell)

`sdm.devices.traits.CameraSound`

This trait belongs to any device that supports sound detection events.

## Fields

There are no fields available for this trait.

## Commands

There are no commands available for this trait.

## Events

### Sound

Sound has been detected by the camera.

#### Sound event

### Payload

```
{
  "eventId" : "3b8f22cc-f8e2-47df-b40b-a6c01ff35270",
  "timestamp" : "2019-01-01T00:00:01Z",
  "resourceUpdate" : {
    "name" : "enterprises/project-id/devices/device-id",
    "events" : {
      "sdm.devices.events.CameraSound.Sound" : {
        "eventSessionId" : "CjY5Y3VKaTZwR3o4Y19YbTVfMF...",
        "eventId" : "si_AsMR13sp9PXQ5m21x9OTJJ5..."
      }
    }
  }
  "userId" : "AVPHwEuBfnPOnTqzVFT4IONX2Qqhu9EJ4ubO-bNnQ-yi",
  "resourceGroup" : [\
    "enterprises/project-id/devices/device-id"\
  ]
}
```

#### Sound event fields

| Field | Description | Data Type |
| --- | --- | --- |
| `eventSessionId` | An ID given to events occurring as part of a single session of<br> related events. May be used for consolidating events. | `string`<br>Example: "CjY5Y3VKaTZwR3o4Y19YbTVfMF..." |
| `eventId` | An ID associated with the event.<br>Use it with the [GenerateImage command](https://developers.google.com/nest/device-access/traits/device/camera-event-image#generateimage) to download the camera image related to this event. | `string`<br>Example: "si\_AsMR13sp9PXQ5m21x9OTJJ5..." |

#### Event payload fields

| Field | Description | Data Type |
| --- | --- | --- |
| `eventId` | The unique identifier for the event. | `string`<br>Example: "3b8f22cc-f8e2-47df-b40b-a6c01ff35270" |
| `timestamp` | The time when the event occurred. | `string`<br>Example: "2019-01-01T00:00:01Z" |
| `resourceUpdate` | An object that details information about the resource update. | `object` |
| `userId` | A unique, obfuscated identifier that represents the user. | `string`<br>Example: "AVPHwEuBfnPOnTqzVFT4IONX2Qqhu9EJ4ubO-bNnQ-yi" |
| `resourceGroup` | An object that indicates resources that might have similar updates to this event. The resource of the event itself (from the `resourceUpdate` object) will always be present in this object. | `object` |

See [Events](https://developers.google.com/nest/device-access/api/events) for more information on the different
types of events and how they work.

## Errors

The following error code(s) may be returned in relation to this trait:

| Error Message | RPC | Troubleshooting |
| --- | --- | --- |
| Camera image is no longer available for download. | `DEADLINE_EXCEEDED` | Event images expire 30 seconds after the event is published. Make sure to download the image prior to expiration. |
| Event id does not belong to the camera. | `FAILED_PRECONDITION` | Use the correct `eventID` returned by the camera event. |

See the [API Error Code Reference](https://developers.google.com/nest/device-access/reference/errors/api) for
the full list of API error codes.

Except as otherwise noted, the content of this page is licensed under the [Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/), and code samples are licensed under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0). For details, see the [Google Developers Site Policies](https://developers.google.com/site-policies). Java is a registered trademark of Oracle and/or its affiliates.

Last updated 2026-06-29 UTC.




\[\[\["Easy to understand","easyToUnderstand","thumb-up"\],\["Solved my problem","solvedMyProblem","thumb-up"\],\["Other","otherUp","thumb-up"\]\],\[\["Missing the information I need","missingTheInformationINeed","thumb-down"\],\["Too complicated / too many steps","tooComplicatedTooManySteps","thumb-down"\],\["Out of date","outOfDate","thumb-down"\],\["Samples / code issue","samplesCodeIssue","thumb-down"\],\["Other","otherDown","thumb-down"\]\],\["Last updated 2026-06-29 UTC."\],\[\],\[\]\]



- ### Engage

  - [Google Developer Program](https://developers.google.com/program)
  - [Google Developer Groups](https://developers.google.com/community)
  - [Google Developer Experts](https://developers.google.com/community/experts)
  - [Accelerators](https://developers.google.com/community/accelerators)
  - [Google Cloud & NVIDIA](https://developers.google.com/community/nvidia)
- ### Connect

  - [Blog](https://googledevelopers.blogspot.com/)
  - [Bluesky](https://bsky.app/profile/developers.google.com)
  - [Instagram](https://www.instagram.com/googlefordevs/)
  - [LinkedIn](https://www.linkedin.com/showcase/googledevelopers/)
  - [X (Twitter)](https://twitter.com/googledevs)
  - [YouTube](https://www.youtube.com/user/GoogleDevelopers)
- ### Build

  - [Android](https://developer.android.com/)
  - [Chrome](https://developer.chrome.com/)
  - [Firebase](https://firebase.google.com/)
  - [Google AI Studio](https://aistudio.google.com/)
  - [Google Antigravity](https://antigravity.google/)
  - [Google Cloud](https://cloud.google.com/)
  - [Google Play](https://play.google.com/console/about/)
  - [View all](https://developers.google.com/products)

[![Google Developers](https://www.gstatic.com/devrel-devsite/prod/v5e941f15ff6710591bee254538202655020220785b40a3f4d932e94adb9f6037/developers/images/lockup-google-for-developers.svg)](https://developers.google.com/)

- [Android](https://developer.android.com/)
- [Chrome](https://developer.chrome.com/home)
- [Firebase](https://firebase.google.com/)
- [Google Cloud Platform](https://cloud.google.com/)
- [Google AI](https://ai.google.dev/)
- [All products](https://developers.google.com/products)

- [Terms](https://developers.google.com/terms/site-terms)
- [Privacy](https://policies.google.com/privacy)
- [Manage cookies](https://developers.google.com/nest/device-access/traits/device/camera-sound#)

- English
- Deutsch
- Español
- Español – América Latina
- Français
- Indonesia
- Italiano
- Polski
- Português – Brasil
- Tiếng Việt
- Türkçe
- Русский
- עברית
- العربيّة
- فارسی
- हिंदी
- বাংলা
- ภาษาไทย
- 中文 – 简体
- 中文 – 繁體
- 日本語
- 한국어
