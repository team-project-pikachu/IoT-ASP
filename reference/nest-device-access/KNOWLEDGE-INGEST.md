# Knowledge Ingest: Nest Device Access (SDM) + Home APIs iOS

## Summary

Firecrawl CLI ingest for M8 Nest cameras + Gemini/ASP acoustic MVP. Pages scraped as markdown; Device Access **console project-list was NOT scraped** (auth wall; owner-gated for `bettyctai@gmail.com`).

- ExtractedAt: 2026-09-08T05:41:55.795815+00:00
- Workflow: firecrawl-knowledge-ingest + firecrawl-map + firecrawl-developer-index (CLI stable)
- Endpoint: `https://smartdevicemanagement.googleapis.com/v1`

## Output

- `reference/nest-device-access/knowledge-ingest.json`
- `reference/nest-device-access/map-links.json` (populated when map completes)
- `reference/nest-device-access/developer-index-quotes.json`
- Per-page `extract-*.md` under this directory
- Raw CLI caches under `.firecrawl/` (gitignored)

## Sections

### SDM API

Source: https://developers.google.com/nest/device-access/api

- REST API for Nest devices via traits + commands.
- All API calls to `https://smartdevicemanagement.googleapis.com/v1` with access token.
- Trait-based model for device information.
- Nest devices authorized through SDM should not be synced to Home Graph for Assistant integrations (avoid conflicts) — per docs.

### Traits index

Source: https://developers.google.com/nest/device-access/traits

Relevant camera traits for M8:

| Trait | SDM type string |
|-------|-----------------|
| CameraSound | `sdm.devices.traits.CameraSound` |
| CameraMotion | `sdm.devices.traits.CameraMotion` |
| CameraPerson | `sdm.devices.traits.CameraPerson` |
| CameraClipPreview | `sdm.devices.traits.CameraClipPreview` |
| CameraEventImage | `sdm.devices.traits.CameraEventImage` |

Events are asynchronous and managed by **Google Cloud Pub/Sub** in a single topic per project ID.

### CameraSound

Source: https://developers.google.com/nest/device-access/traits/device/camera-sound

```
- [CameraClipPreview](https://developers.google.com/nest/device-access/traits/device/camera-clip-preview)
- [CameraSound](https://developers.google.com/nest/device-access/traits/device/camera-sound)
# CameraSound Schema
`sdm.devices.traits.CameraSound`
"sdm.devices.events.CameraSound.Sound" : {
```

### CameraClipPreview

Source: https://developers.google.com/nest/device-access/traits/device/camera-clip-preview

```
- [CameraClipPreview](https://developers.google.com/nest/device-access/traits/device/camera-clip-preview)
- [CameraSound](https://developers.google.com/nest/device-access/traits/device/camera-sound)
- [ClipPreview](https://developers.google.com/nest/device-access/traits/device/camera-clip-preview#clippreview)
- [ClipPreview](https://developers.google.com/nest/device-access/traits/device/camera-clip-preview#clippreview)
# CameraClipPreview Schema    Stay organized with collections      Save and categorize content based on your preferences.
`sdm.devices.traits.CameraClipPreview`
### ClipPreview
#### ClipPreview event
"sdm.devices.events.CameraClipPreview.ClipPreview" : {
#### ClipPreview event fields
```

### Client libraries

Source: https://developers.google.com/nest/device-access/api/libraries

SDM API client libraries exist for Go, Java, Python, Node, etc. (HTTP+JSON). Pin versions in real integrations — never invent `@latest` wiring in-repo.

### Home APIs iOS get-started (retained)

Source: https://developers.home.google.com/apis/ios/get-started

Flow (docs): Sample App → Get SDK → OAuth → Initialize home → Integrate Structure/Device/Automation/Commissioning → Test → Register/Launch (coming soon). Distinct from SDM Device Access but complementary for iOS HomeNestAlarm feature.

## Failed Or Restricted Pages

| URL | Status |
|-----|--------|
| https://console.nest.google.com/device-access/project-list | **Not scraped** — owner console / auth wall. Document only. Owner: bettyctai@gmail.com |

## Developer-index quoted passages


### `web:https://www.home-assistant.io/integrations/nest/`

- URL: https://www.home-assistant.io/integrations/nest/
- Passage: {'text': 'The Nest integration subscribes a Google Pub/sub subscription to listen for camera motion or person events. ... If the Pub/Sub topic starts with projects/sdm ...'}

### `web:https://stackoverflow.com/questions/76562492/google-nest-camera-events-not-published-to-device-access-console-topic`

- URL: https://stackoverflow.com/questions/76562492/google-nest-camera-events-not-published-to-device-access-console-topic
- Passage: {'text': 'I created a Pub/Sub Subscription in the google cloud console but is not receiving any messages. I issued the sdm api listDevices command, but no ...Google PubSub Subscriber issues with Google SDM API (Nest Devices)Googler Nest API - Get Motion video clip from Resource EventMore results from stackoverflow.com'}

### `web:https://allenporter.github.io/python-google-nest-sdm/`

- URL: https://allenporter.github.io/python-google-nest-sdm/
- Passage: {'text': 'Library for using the Google Nest SDM API. ... google_nest_subscriber : A wrapper around the pub/sub system for efficiently listening to changes in device state.'}

### `web:https://plugins.hoobs.org/plugin/homebridge-google-nest-sdm`

- URL: https://plugins.hoobs.org/plugin/homebridge-google-nest-sdm
- Passage: {'text': 'Note the "+https://www.googleapis.com/auth/pubsub" on the end. This is so you will have access to events. FAQ. Q: I don\'t see camera snapshots ...'}

### `web:https://www.openhab.org/addons/bindings/nest/`

- URL: https://www.openhab.org/addons/bindings/nest/
- Passage: {'text': 'After configuring the SDM parameters, an SDM Account Thing can be updated so it can listen to SDM events using Pub/Sub. This is required if you want to download ...'}

### `web:https://issuetracker.google.com/358755975`

- URL: https://issuetracker.google.com/358755975
- Passage: {'text': 'Successfully follow instructions to setup a camera using SDM API; Verify pub/sub events are published to topic (for over a year); Onboard an ...'}

### `web:https://groups.google.com/g/cloud-pubsub-discuss/c/wAaqgQ36rpE`

- URL: https://groups.google.com/g/cloud-pubsub-discuss/c/wAaqgQ36rpE
- Passage: {'text': 'I am using the new Google SDM API to listen to events that occur on my Nest thermostat. I am listening to these events through a pub/sub topic.'}

### `readme:allenporter/python-google-nest-sdm`

- URL: https://github.com/allenporter/python-google-nest-sdm
- Passage: {'text': '# Fetching Data\n\n# Subscriptions\n- Create the topic:\n  - Enable Pub/Sub and note the full `topic` based on the `project_id`', 'citation_url': 'https://raw.githubusercontent.com/allenporter/python-google-nest-sdm/HEAD/README.md'}

### `web:https://medium.com/@tamirmayer/google-nest-camera-internal-api-fdf9dc3ce167`

- URL: https://medium.com/@tamirmayer/google-nest-camera-internal-api-fdf9dc3ce167
- Passage: {'text': "It's called “Smart Device Management API” That is the API being used in Home Assistant. Create your project on the Google Nest Device Access ..."}

### `web:https://developers.google.com/nest/device-access/api`

- URL: https://developers.google.com/nest/device-access/api
- Passage: {'text': 'The SDM API is a REST API that lets you manage Google Nest devices by viewing their traits and executing commands. Camera Camera (battery)'}

### `web:https://community.home-assistant.io/t/add-nest-device-access-through-the-smart-device-management-sdm-api/230187`

- URL: https://community.home-assistant.io/t/add-nest-device-access-through-the-smart-device-management-sdm-api/230187
- Passage: {'text': 'Google has introduced support for Nest integration through their Smart Device Management (SDM) API. It costs $5 to register, ...'}

### `web:https://apis.io/collections/google-nest/postman-google-nest-devices-api/`

- URL: https://apis.io/collections/google-nest/postman-google-nest-devices-api/
- Passage: {'text': 'The Smart Device Management (SDM) API is a REST API that allows developers to manage Google Nest devices. It provides access to device traits and commands for ...'}


## Sources

- https://developers.google.com/nest/device-access/api
- https://developers.google.com/nest/device-access/traits
- https://developers.google.com/nest/device-access/traits/device/camera-clip-preview
- https://developers.google.com/nest/device-access/api/libraries
- https://developers.google.com/nest/device-access/traits/device/camera-sound
- https://developers.google.com/nest/device-access/traits/device/camera-motion
- https://developers.google.com/nest/device-access/traits/device/camera-event-image
- https://developers.home.google.com/apis/ios/get-started
- https://developers.home.google.com/apis/ios/get-started
- https://console.nest.google.com/device-access/project-list (owner-gated; not scraped)

## Rerun Inputs

```
workflow: firecrawl-knowledge-ingest
url: https://developers.google.com/nest/device-access
format: markdown+json
max_pages: 80
console: skip (owner bettyctai@gmail.com)
```

## ASP / M8 wiring notes

- Event classes in app: `sound_burst` | `glass_shatter` | SDM `CameraSound` events | ClipPreview session correlation
- Gemini Enterprise detector (gcloud) classifies ASP micDiff / Nest event payloads → escalate louder alarm
- Platforms: Vercel PWA, iOS Xcode/Swift (`native/IoTASPHome`), Swift Playground stub
