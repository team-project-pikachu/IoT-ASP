# MVP closed-issue log

Append-only audit of **closed** GitHub issues for IoT-ASP.
Maintained by `scripts/mvp_closed_log_append.sh` ([#68](https://github.com/team-project-pikachu/IoT-ASP/issues/68); #65 closed as duplicate).
Optional Action: `.github/workflows/mvp-closed-log.yml` — prefers PR branch `automation/mvp-closed-log` under main protection; optional `MVP_CLOSED_LOG_PUSH_MAIN=1` for direct main push. Soft-fails with a notice if push is blocked — then use the script.

Do **not** paste issue bodies (may contain operator notes). Titles + metadata only.
| Closed (UTC) | Issue | Title | Milestone | Labels | Reason |
|--------------|------:|-------|-----------|--------|--------|
| 2026-09-08 | #12 | LLM autoroute: Gemini continuous monitor + audio engineering | M6 — LLM autoroute (Gemini) | `enhancement` | COMPLETED |
| 2026-09-08 | #9 | SensorKit / native iOS shell + edge companions (research) | M5 — SensorKit / native iOS shell (research) | `parked,research` | COMPLETED |
| 2026-09-08 | #13 | Autoroute multi-LLM registry (post-Gemini) | M6 — LLM autoroute (Gemini) | `enhancement,parked` | COMPLETED |
| 2026-09-08 | #17 | Colab + Gemini Enterprise data processing pipeline | M6 — LLM autoroute (Gemini) | `enhancement` | COMPLETED |
| 2026-09-08 | #16 | Navier–Stokes / seismo-acoustic priors for vib→algorithm routing | - | `enhancement,research` | COMPLETED |
| 2026-09-08 | #21 | Google Home Wi-Fi autorotate now; cellular later | - | `parked,research` | COMPLETED |
| 2026-09-08 | #23 | AI Edge Portal optional packaging | - | `parked,docs` | COMPLETED |
| 2026-09-08 | #20 | Timestore SciPy ≥16-param + Fairfax weather + ciphers | - | `enhancement,parked` | COMPLETED |
| 2026-09-08 | #37 | Vercel webhooks for hop-ultrasonic deploy notifications | - | `enhancement,docs` | COMPLETED |
| 2026-09-08 | #44 | Web PWA: impulse → blast volume (micDiff/accel) | - | `enhancement` | NOT_PLANNED |
| 2026-09-08 | #45 | Web PWA: alarm-system reactivity (armed→triggered→sustaining→cleared) | - | `enhancement` | NOT_PLANNED |
| 2026-09-08 | #46 | Impulse → blast volume (web + native) | - | `enhancement` | NOT_PLANNED |
| 2026-09-08 | #47 | Alarm-system reactivity (armed→triggered→sustaining→cleared) | - | `enhancement` | NOT_PLANNED |
| 2026-09-08 | #50 | Impulse → blast volume (web + native) | - | `enhancement` | NOT_PLANNED |
| 2026-09-08 | #51 | Alarm-system reactivity (armed→triggered→sustaining→cleared) | - | `enhancement` | NOT_PLANNED |
| 2026-09-08 | #48 | iOS app + Apple Watch companion (Xcode targets) | - | `enhancement,research` | NOT_PLANNED |
| 2026-09-08 | #52 | iOS app + Apple Watch companion (Xcode targets) | - | `enhancement,research` | NOT_PLANNED |
| 2026-09-08 | #49 | Anker Soundcore manufacturer specs (fleet A2DP nodes) | - | `research,docs` | NOT_PLANNED |
| 2026-09-08 | #53 | Anker Soundcore manufacturer specs (fleet A2DP nodes) | - | `research,docs` | NOT_PLANNED |
## Backfill / append
```bash
# Single issue (after close)
bash scripts/mvp_closed_log_append.sh 37
# Rebuild table body from all closed issues (keeps header)
bash scripts/mvp_closed_log_append.sh --backfill
```
Append-only. Format: `YYYY-MM-DD | #N | title | one-line outcome`  
Convention: [mvp-roadmap.md](mvp-roadmap.md) · Automation: [#65](https://github.com/team-project-pikachu/IoT-ASP/issues/65)
## Log
2026-09-08 | #9 | SensorKit / native iOS shell + edge companions (research) | research closeout; impl parked → #41
2026-09-08 | #12 | LLM autoroute: Gemini continuous monitor + audio engineering | design/dry-run wave closed; prod deploy → #60
2026-09-08 | #13 | Autoroute multi-LLM registry (post-Gemini) | design sketch only; no prod non-Gemini
2026-09-08 | #16 | Navier–Stokes / seismo-acoustic priors for vib→algorithm routing | priors docs/evidence closed this wave
2026-09-08 | #17 | Colab + Gemini Enterprise data processing pipeline | pipeline docs/notebooks closed; live GCS → #26
2026-09-08 | #20 | Timestore SciPy ≥16-param + Fairfax weather + ciphers | implemented (`packages/algo-timestore/`)
2026-09-08 | #21 | Google Home Wi-Fi autorotate now; cellular later | parked research closed; see docs/connectivity-wifi.md
2026-09-08 | #23 | AI Edge Portal optional packaging | parked; docs/ai-edge-portal.md
2026-09-08 | #37 | Vercel webhooks for hop-ultrasonic deploy notifications | docs + dispatch stub landed
2026-09-08 | #44 | Web PWA: impulse → blast volume (micDiff/accel) | duplicate of #42
2026-09-08 | #45 | Web PWA: alarm-system reactivity (armed→triggered→sustaining→cleared) | duplicate of #42
2026-09-08 | #46 | Impulse → blast volume (web + native) | duplicate of #42/#44
2026-09-08 | #47 | Alarm-system reactivity (armed→triggered→sustaining→cleared) | duplicate of #42/#45
2026-09-08 | #48 | iOS app + Apple Watch companion (Xcode targets) | duplicate of #41
2026-09-08 | #49 | Anker Soundcore manufacturer specs (fleet A2DP nodes) | duplicate of #43
2026-09-08 | #50 | Impulse → blast volume (web + native) | duplicate of #42
2026-09-08 | #51 | Alarm-system reactivity (armed→triggered→sustaining→cleared) | duplicate of #42
2026-09-08 | #52 | iOS app + Apple Watch companion (Xcode targets) | duplicate of #41
2026-09-08 | #53 | Anker Soundcore manufacturer specs (fleet A2DP nodes) | duplicate of #43
