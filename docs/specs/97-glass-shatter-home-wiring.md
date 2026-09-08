# #97 — Glass shatter Home app wiring + Automation/notify TODO

## Status

implemented stub — Glass Shatter tab + notify TODO protocol

## Goal

Wire Glass Shatter tab + `GlassShatterPipeline` Home Automation / Nest notification hook TODOs.
Cross-link Nest premium + louder alarm path.

## Shipped

- `GlassShatterFeatureView` tab in `HomeNestRootView`
- `GlassShatterPipeline` → escalate + camera snapshot stub
- `HomeAutomationNotifyClient` / `TodoHomeAutomationNotifyClient` (pending, not delivered)
- Louder path via `EscalatingAlarmController` (glass hot-start ≥70)

## Remaining scope

Live GoogleHomeSDK Automation API + Nest premium notify after owner OAuth.

## Acceptance

- Simulate glass shatter → `homeNotifyPending == true`, `volBlast` / hotter `targetVol`
- `make home-ios-build`
