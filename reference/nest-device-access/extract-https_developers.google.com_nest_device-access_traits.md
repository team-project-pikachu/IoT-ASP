# Extract

Source: https://developers.google.com/nest/device-access/traits

ExtractedAt: 2026-09-08T05:39:00.194323+00:00

---

[Skip to main content](https://developers.google.com/nest/device-access/traits#main-content)

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

# Traits    Stay organized with collections      Save and categorize content based on your preferences.

![Spark icon](https://developers.google.com/_static/images/icons/spark.svg)

## Page Summary

outlined\_flag

- The Smart Device Management API allows you to interact with Nest devices through traits, commands, and events.

- Traits represent device capabilities and their associated data, such as temperature or humidity, and are categorized by device type like Thermostat or Camera.

- Commands are used to control devices, for instance, changing the thermostat mode, while events provide asynchronous notifications about device state changes.

- You can access device information and traits through a GET request to the specified API endpoint using the device ID.

- Google Cloud Pub/Sub manages events and delivers them to a dedicated topic for each project ID, allowing you to stay updated on device activity.


A **trait** in the SDM API comprises **fields**, **commands**, and **events**.

All calls to the SDM API should use the following
endpoint:

`https://smartdevicemanagement.googleapis.com/v1`

## Fields

Fields are values with common data types, such as a number or a string. For example, a field
might contain a the current mode or the ambient humidity of a Google Nest Thermostat.

Traits and fields can be viewed with a `GET` call to the desired API endpoint:

```
GET /enterprises/project-id/devices/device-id
{
  "name" : "enterprises/project-id/devices/device-id",
  "type" : "sdm.devices.types.device-type",
  "traits" : { ... },
  "parentRelations" : [\
    {\
      "parent" : "enterprises/project-id/structures/structure-id/rooms/room-id",\
      "displayName" : "Lobby"\
    }\
  ]
}
```

### Device types

The `sdm.devices.types.device-type` returned by the SDM API should not be used
to deduce or infer functionality of the actual device it is assigned to. There is no guarantee
that a device type will remain stable for a specific device as more features are added to the SDM
API. Instead, use the returned traits for the device.

### parentRelations

The `parentRelations` object represents the parent resource of the current resource,
either a structure or room. Display name corresponds to the `customName` field of the
[Info trait](https://developers.google.com/nest/device-access/traits/structure/info)
for devices with a structure parent or the
[RoomInfo trait](https://developers.google.com/nest/device-access/traits/structure/room-info) for devices with a
room parent.

## Commands

Commands are requests associated with a trait. For example, changing the current mode or
temperature setpoint on a Google Nest Thermostat.

A command is sent by an `executeCommand` API call:

```
POST /enterprises/project-id/devices/device-id:executeCommand
{
  "command" : "command-name",
  "params" : {
    "field" : "value"
  }
}
```

Most responses to a command are a simple success or failure. See the individual trait guides for
specific command usage examples.

## Events

Events are asynchronous and managed by Google Cloud Pub/Sub in a single topic per
Project ID.

Events are sent by default for any change in the value of a trait field. They can also be sent in
response to specific device actions or changes in resource assignments. See
[Events](https://developers.google.com/nest/device-access/api/events)
for more information.

## Trait categories

### Structure

| Traits |
| --- |
| [Info](https://developers.google.com/nest/device-access/traits/structure/info) | |     |
| --- |
| `sdm.structures.traits.Info` |
| This trait belongs to any structure for structure-related information. | |
| [RoomInfo](https://developers.google.com/nest/device-access/traits/structure/room-info) | |     |
| --- |
| `sdm.structures.traits.RoomInfo` |
| This trait belongs to any room for room-related information. | |

### Device

| Traits |
| --- |
| [Connectivity](https://developers.google.com/nest/device-access/traits/device/connectivity) | |     |
| --- |
| `sdm.devices.traits.Connectivity` |
| This trait belongs to any device that has connectivity information. | |
| [Fan](https://developers.google.com/nest/device-access/traits/device/fan) | |     |
| --- |
| `sdm.devices.traits.Fan` |
| This trait belongs to any device that has the system ability to control the fan. | |
| [Humidity](https://developers.google.com/nest/device-access/traits/device/humidity) | |     |
| --- |
| `sdm.devices.traits.Humidity` |
| This trait belongs to any device that has a sensor to measure humidity. | |
| [Info](https://developers.google.com/nest/device-access/traits/device/info) | |     |
| --- |
| `sdm.devices.traits.Info` |
| This trait belongs to any device for device-related information. | |
| [Settings](https://developers.google.com/nest/device-access/traits/device/settings) | |     |
| --- |
| `sdm.devices.traits.Settings` |
| This trait belongs to any device for device-related settings information. | |
| [Temperature](https://developers.google.com/nest/device-access/traits/device/temperature) | |     |
| --- |
| `sdm.devices.traits.Temperature` |
| This trait belongs to any device that has a sensor to measure temperature. | |

### Thermostat

| Traits |
| --- |
| [ThermostatEco](https://developers.google.com/nest/device-access/traits/device/thermostat-eco) | |     |
| --- |
| `sdm.devices.traits.ThermostatEco` |
| This trait belongs to device types of THERMOSTAT that support ECO modes. | |
| [ThermostatHvac](https://developers.google.com/nest/device-access/traits/device/thermostat-hvac) | |     |
| --- |
| `sdm.devices.traits.ThermostatHvac` |
| This trait belongs to device types of THERMOSTAT that can report HVAC details. | |
| [ThermostatMode](https://developers.google.com/nest/device-access/traits/device/thermostat-mode) | |     |
| --- |
| `sdm.devices.traits.ThermostatMode` |
| This trait belongs to device types of THERMOSTAT that support different thermostat modes. | |
| [ThermostatTemperatureSetpoint](https://developers.google.com/nest/device-access/traits/device/thermostat-temperature-setpoint) | |     |
| --- |
| `sdm.devices.traits.ThermostatTemperatureSetpoint` |
| This trait belongs to device types of THERMOSTAT that support setting target temperature and temperature range. | |

### Camera

| Traits |
| --- |
| [CameraClipPreview](https://developers.google.com/nest/device-access/traits/device/camera-clip-preview) | |     |
| --- |
| `sdm.devices.traits.CameraClipPreview` |
| This trait belongs to any device that supports the download of a clip preview. | |
| [CameraEventImage](https://developers.google.com/nest/device-access/traits/device/camera-event-image) | |     |
| --- |
| `sdm.devices.traits.CameraEventImage` |
| This trait belongs to any device that supports generation of images from events. | |
| [CameraImage](https://developers.google.com/nest/device-access/traits/device/camera-image) | |     |
| --- |
| `sdm.devices.traits.CameraImage` |
| This trait belongs to any device that supports taking images. | |
| [CameraLiveStream](https://developers.google.com/nest/device-access/traits/device/camera-live-stream) | |     |
| --- |
| `sdm.devices.traits.CameraLiveStream` |
| This trait belongs to any device that supports live streaming. | |
| [CameraMotion](https://developers.google.com/nest/device-access/traits/device/camera-motion) | |     |
| --- |
| `sdm.devices.traits.CameraMotion` |
| This trait belongs to any device that supports motion detection events. | |
| [CameraPerson](https://developers.google.com/nest/device-access/traits/device/camera-person) | |     |
| --- |
| `sdm.devices.traits.CameraPerson` |
| This trait belongs to any device that supports person detection events. | |
| [CameraSound](https://developers.google.com/nest/device-access/traits/device/camera-sound) | |     |
| --- |
| `sdm.devices.traits.CameraSound` |
| This trait belongs to any device that supports sound detection events. | |

### Doorbell

| Traits |
| --- |
| [DoorbellChime](https://developers.google.com/nest/device-access/traits/device/doorbell-chime) | |     |
| --- |
| `sdm.devices.traits.DoorbellChime` |
| This trait belongs to any device that supports a doorbell chime and related press events. | |

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
- [Manage cookies](https://developers.google.com/nest/device-access/traits#)

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
