# MVP closed-issue log

Durable audit trail of **closed** GitHub issues for the public MVP roadmap.
Complements Project 5 (board UI is not the sole record). Pair with `docs/mvp-roadmap.md` (#69).

**Format (one line per closed issue, newest first preferred):**
```
| YYYY-MM-DD | #N | Title (truncated ≤80) | labels | closer |
- **Date:** `closed_at` date (UTC) or the day the log line was written.
- **#N / Title:** issue number and title; do **not** copy full issue bodies (no PII risk).
- **labels:** comma-joined label names at close time when known; else `-`.
- **closer:** GitHub login that closed the issue when available; else `unknown` / script operator.
No secrets, no street addresses, no raw telemetry payloads.
## How to append
```bash
# Append a single closed issue (uses gh API)
bash scripts/mvp_closed_log_append.sh 65
# Backfill all currently closed issues (idempotent by #N)
bash scripts/mvp_closed_log_append.sh --backfill
Optional workflow: `.github/workflows/mvp-closed-log.yml` (see script header).
Repo default Actions permissions are often `contents: read`; if auto-push to `main` is blocked by rulesets, run the CLI manually or open a short-lived automation PR branch.
## Log
| Date | Issue | Title | Labels | Closer |
|------|------:|-------|--------|--------|
| 2026-09-08 | #65 | Automate closed-issue → docs/mvp-closed-log.md append | enhancement, docs | 1digitaldesign |
| 2026-09-08 | #53 | Anker Soundcore manufacturer specs (fleet A2DP nodes) | research, docs | unknown |
| 2026-09-08 | #52 | iOS app + Apple Watch companion (Xcode targets) | enhancement, research | unknown |
| 2026-09-08 | #51 | Alarm-system reactivity (armed→triggered→sustaining→cleared) | enhancement | unknown |
| 2026-09-08 | #50 | Impulse → blast volume (web + native) | enhancement | unknown |
| 2026-09-08 | #49 | Anker Soundcore manufacturer specs (fleet A2DP nodes) | research, docs | unknown |
| 2026-09-08 | #48 | iOS app + Apple Watch companion (Xcode targets) | enhancement, research | unknown |
| 2026-09-08 | #47 | Alarm-system reactivity (armed→triggered→sustaining→cleared) | enhancement | unknown |
| 2026-09-08 | #46 | Impulse → blast volume (web + native) | enhancement | unknown |
| 2026-09-08 | #45 | Web PWA: alarm-system reactivity (armed→triggered→sustaining→cleared) | enhancement | unknown |
| 2026-09-08 | #44 | Web PWA: impulse → blast volume (micDiff/accel) | enhancement | unknown |
| 2026-09-08 | #37 | Vercel webhooks for hop-ultrasonic deploy notifications | enhancement, docs | unknown |
| 2026-09-08 | #23 | AI Edge Portal optional packaging | parked, docs | unknown |
| 2026-09-08 | #21 | Google Home Wi-Fi autorotate now; cellular later | parked, research | unknown |
| 2026-09-08 | #20 | Timestore SciPy ≥16-param + Fairfax weather + ciphers | enhancement, parked | unknown |
| 2026-09-08 | #17 | Colab + Gemini Enterprise data processing pipeline | enhancement | unknown |
| 2026-09-08 | #16 | Navier–Stokes / seismo-acoustic priors for vib→algorithm routing | enhancement, research | unknown |
| 2026-09-08 | #13 | Autoroute multi-LLM registry (post-Gemini) | enhancement, parked | unknown |
| 2026-09-08 | #12 | LLM autoroute: Gemini continuous monitor + audio engineering | enhancement | unknown |
| 2026-09-08 | #9 | SensorKit / native iOS shell + edge companions (research) | parked, research | unknown |
Append-only. Format: `YYYY-MM-DD | #N | title | one-line outcome`  
Convention: [mvp-roadmap.md](mvp-roadmap.md) · Automation: [#65](https://github.com/team-project-pikachu/IoT-ASP/issues/65)
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
