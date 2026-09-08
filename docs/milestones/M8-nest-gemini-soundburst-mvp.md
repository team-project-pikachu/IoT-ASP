# M8 — Nest cameras + Gemini sound-burst + glass shatter MVP

Milestone: Nest cameras + Gemini sound-burst → louder alarm, with **glass shatter** as a
first-class event class (`sound_burst` | `glass_shatter` | `unknown`).

## Detector wire (#96)

```
Nest / ASP mic features → StubBurstDetectClient / gemini-burst-detect
                         → { burst, eventClass, confidence, escalateDb }
```

Python stub JSON keys match Swift `AcousticDetectResult`.

| Issue | Slice |
|-------|-------|
| [#96](https://github.com/team-project-pikachu/IoT-ASP/issues/96) | Model/event class + stub thresholds |
| [#97](https://github.com/team-project-pikachu/IoT-ASP/issues/97) | Home app Glass Shatter tab + Automation/notify TODO |

Hold / Manual clears blast escalation. No secrets in git.

## Home wiring (#97)

Glass Shatter tab → `GlassShatterPipeline` → `TodoHomeAutomationNotifyClient` (pending) + louder `EscalatingAlarmController`.
