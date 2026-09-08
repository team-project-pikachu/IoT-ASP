# ISSUE-45 — Web PWA alarm reactivity

**Status:** working slice (PR2) — armed→triggered→sustaining→cleared→armed with quiet hysteresis + cleared latch; `alarmTick` sustains while `soundBurst`/`lastBurstAt` hot; restores `volBeforeBlast` on clear; fleet cards show alarm.

## Didn't

- Native Watch WCSession production polish (see #41)
