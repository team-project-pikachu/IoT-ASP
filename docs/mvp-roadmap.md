# MVP feature roadmap → GitHub issues

Living map for the **web MVP ship path** (phones + Soundcore A2DP + Vercel PWA + GCP/ADK control plane).  
Parked items stay labeled `parked` on GitHub; do not treat them as ship blockers.

**Board:** [Project 5](https://github.com/orgs/team-project-pikachu/projects/5) · **Issues:** https://github.com/team-project-pikachu/IoT-ASP/issues  
**Closed log:** [mvp-closed-log.md](mvp-closed-log.md) (append on close — workflow [#65](https://github.com/team-project-pikachu/IoT-ASP/issues/65))

## MVP pillars

| Pillar | Intent |
|--------|--------|
| **Web blaster** | Public static PWA; 3 phones; incoherent hops; C1 A2DP only |
| **Deploy / CI** | Actions gates → Vercel dev/test/prod; main protected |
| **Control plane** | ADK/Gemini autoroute + live patch/telemetry URLs |
| **Telemetry** | schemaVersion-1 beacons, structured fleet logs, Colab/GCS |
| **Audio / ASP core** | Carriers, suddenFreq, impulse→blast, alarm states, HW honesty |
| **Sensors** | DeviceMotion / mic (web); native/SensorKit later |
| **V&V** | SEBoK matrix pass for C1–C6 + contract before calling MVP done |

## Milestone → issues (ship path)

| Milestone | MVP issues (open or done) | Notes |
|-----------|---------------------------|-------|
| **M0 — Public web blaster** | [#1](https://github.com/team-project-pikachu/IoT-ASP/issues/1) · [#61](https://github.com/team-project-pikachu/IoT-ASP/issues/61) · [#62](https://github.com/team-project-pikachu/IoT-ASP/issues/62) · [#43](https://github.com/team-project-pikachu/IoT-ASP/issues/43) · [#42](https://github.com/team-project-pikachu/IoT-ASP/issues/42) | Live URL shipped; wire backend URLs + field/e2e acceptance remain. **Not ship blockers:** [#10](https://github.com/team-project-pikachu/IoT-ASP/issues/10) React rewrite (parked/deferred); [#11](https://github.com/team-project-pikachu/IoT-ASP/issues/11) React fleet polish deferred — static fleet strip already on `main` |
| **M1 — Seeds** | [#2](https://github.com/team-project-pikachu/IoT-ASP/issues/2) | Spec says implemented on branch; still open/`parked` on GitHub — reconcile label when merging |
| **M2 — Monitoring** | [#3](https://github.com/team-project-pikachu/IoT-ASP/issues/3) | Same reconcile note as M1 |
| **M3 — Vibration** | [#4](https://github.com/team-project-pikachu/IoT-ASP/issues/4) · [#5](https://github.com/team-project-pikachu/IoT-ASP/issues/5) · [#6](https://github.com/team-project-pikachu/IoT-ASP/issues/6) | Parked for full arming UI; partial priors shipped |
| **M4 — RLHF ±** | [#7](https://github.com/team-project-pikachu/IoT-ASP/issues/7) · [#8](https://github.com/team-project-pikachu/IoT-ASP/issues/8) | Parked (post-MVP) |
| **M5 — Native / SensorKit** | [#41](https://github.com/team-project-pikachu/IoT-ASP/issues/41) · ~~#9~~ | Research #9 closed; impl → #41 |
| **M6 — LLM autoroute** | [#60](https://github.com/team-project-pikachu/IoT-ASP/issues/60) · ~~#12~~ · ~~#16~~ · ~~#17~~ | Deploy ADK to Cloud Run/Agent Engine; design closed |
| **M7 — Edge** | [#14](https://github.com/team-project-pikachu/IoT-ASP/issues/14) · [#15](https://github.com/team-project-pikachu/IoT-ASP/issues/15) · [#18](https://github.com/team-project-pikachu/IoT-ASP/issues/18) · [#39](https://github.com/team-project-pikachu/IoT-ASP/issues/39) | Parked hardware / research |
| **Ship / infra** | [#27](https://github.com/team-project-pikachu/IoT-ASP/issues/27) · [#63](https://github.com/team-project-pikachu/IoT-ASP/issues/63) · [#65](https://github.com/team-project-pikachu/IoT-ASP/issues/65) · ~~#37~~ · [#34](https://github.com/team-project-pikachu/IoT-ASP/issues/34) | Secrets + ruleset + closed-log automation |
| **Telemetry / DSP** | [#22](https://github.com/team-project-pikachu/IoT-ASP/issues/22) · [#26](https://github.com/team-project-pikachu/IoT-ASP/issues/26) · [#25](https://github.com/team-project-pikachu/IoT-ASP/issues/25) | Enrichment + live GCS + LF/AEC honesty |
| **V&V** | [#64](https://github.com/team-project-pikachu/IoT-ASP/issues/64) | Matrix C1–C6 / SCH1 / HOLD1 → `pass` |

## Suggested MVP close order

```text
#27 secrets → #60 ADK deploy → #61 wire URLs → #62 field/e2e → #63 ruleset → #64 V&V → #65 log automation (land with this doc)
     ↘ #42 impulse/alarm (web)   ↘ #22/#26 telemetry polish   ↘ #43 specs (docs)
```

Native [#41](https://github.com/team-project-pikachu/IoT-ASP/issues/41) and parked M3–M4 / edge issues are **not** required to call web MVP done.

## Closed-issue logging convention

When an issue **closes**:

1. Automation ([#65](https://github.com/team-project-pikachu/IoT-ASP/issues/65), workflow `mvp-closed-log.yml`) appends one line to [mvp-closed-log.md](mvp-closed-log.md).
2. Line format: `YYYY-MM-DD | #N | <title> | <one-line outcome>`
3. Outcome = first line of the **closing-associated** timeline comment if present; else the issue title (never an unrelated later comment).
4. Do **not** delete historical rows. Duplicates of the same `#N` are skipped.
5. Manual append: `bash scripts/mvp_closed_log_append.sh <n> [outcome…]`
6. Bulk backfill: `bash scripts/mvp_closed_log_append.sh --backfill` (paginated `gh` closed-issue list; idempotent)

Update this roadmap table only when milestones/issue ownership change — not on every close (the log is the chronological record).

## Specs / status artifacts

- Feature specs: [specs/README.md](specs/README.md)
- Balanced stub board: [issues/BALANCED-BUILD-STATUS.md](issues/BALANCED-BUILD-STATUS.md)
- V&V matrix: [../.vv/matrix.md](../.vv/matrix.md)
- Constraints: [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md)
