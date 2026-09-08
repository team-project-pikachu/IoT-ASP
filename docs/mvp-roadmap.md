# MVP feature roadmap — milestones → issues

Canonical map for Project 5 ([board](https://github.com/orgs/team-project-pikachu/projects/5)).
Parked work uses the `parked` label. Feature specs: [`docs/specs/`](specs/README.md).
Live app: https://hop-ultrasonic-1digital-design.vercel.app/
**Constraints:** **C1** iOS native A2DP only (no Web Bluetooth TX). **C2** Pi USB-C field node is not MVP web ([#14](https://github.com/team-project-pikachu/IoT-ASP/issues/14)).
Tracked by [#69](https://github.com/team-project-pikachu/IoT-ASP/issues/69). Closed audit trail: [`mvp-closed-log.md`](mvp-closed-log.md) ([#68](https://github.com/team-project-pikachu/IoT-ASP/issues/68); #65 closed as duplicate).

### Session batch (2026-09-08)
Chat opened #60–#65, #67–#69 (#65 → dup of #68; #67 closed via [#78](https://github.com/team-project-pikachu/IoT-ASP/pull/78)). Canonical session audit: [`mvp-session-2026-09-08.md`](mvp-session-2026-09-08.md) · PR [#79](https://github.com/team-project-pikachu/IoT-ASP/pull/79).
## M0–M5 (README roadmap)
| Milestone | Pillar | Issues | Specs / notes |
|-----------|--------|--------|----------------|
| **M0** — Public web blaster | Ship static hop PWA (incoherent hops, 1:1 phone↔Soundcore, Vercel URL) | [#1](https://github.com/team-project-pikachu/IoT-ASP/issues/1) (active); [#61](https://github.com/team-project-pikachu/IoT-ASP/issues/61)/[#62](https://github.com/team-project-pikachu/IoT-ASP/issues/62) ship gates; [#10](https://github.com/team-project-pikachu/IoT-ASP/issues/10)/[#11](https://github.com/team-project-pikachu/IoT-ASP/issues/11) React rewrite (`parked`) | [`01-m0-public-blaster.md`](specs/01-m0-public-blaster.md), [`10-11-react-rewrite.md`](specs/10-11-react-rewrite.md) |
| **M1** — Max-entropy seeds | Crypto-mixed seeds, min Δf, stagger, Reseed UI | [#2](https://github.com/team-project-pikachu/IoT-ASP/issues/2) (`parked`) | [`02-max-entropy-seeds.md`](specs/02-max-entropy-seeds.md) |
| **M2** — Continuous monitoring | Watchdog + monitor panel while Signal on | [#3](https://github.com/team-project-pikachu/IoT-ASP/issues/3) (`parked`) | [`03-continuous-monitoring-watchdog.md`](specs/03-continuous-monitoring-watchdog.md) |
| **M3** — Vibration response | Physical and/or acoustic vib → hop rotation | [#4](https://github.com/team-project-pikachu/IoT-ASP/issues/4)/[#5](https://github.com/team-project-pikachu/IoT-ASP/issues/5)/[#6](https://github.com/team-project-pikachu/IoT-ASP/issues/6) (`parked`) | [`04-06-vibration-channels.md`](specs/04-06-vibration-channels.md) |
| **M4** — RLHF ± | Good/bad taps → policy θ | [#7](https://github.com/team-project-pikachu/IoT-ASP/issues/7)/[#8](https://github.com/team-project-pikachu/IoT-ASP/issues/8) (`parked`) | [`07-08-rlhf-loops.md`](specs/07-08-rlhf-loops.md) |
| **M5** — SensorKit research | Native entitlement path (web ≠ SensorKit) | [#9](https://github.com/team-project-pikachu/IoT-ASP/issues/9) (closed research); impl track [#41](https://github.com/team-project-pikachu/IoT-ASP/issues/41) | [`sensorkit-research-closeout.md`](sensorkit-research-closeout.md), [`native-xcode.md`](native-xcode.md) |
## Suggested MVP close order (web ship path)
```text
#27 secrets → #60 ADK deploy → #61 wire URLs → #62 field/e2e → #63 ruleset → #64 V&V → #68 log automation
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
| **M0 — Public web blaster** | [#1](https://github.com/team-project-pikachu/IoT-ASP/issues/1) · [#61](https://github.com/team-project-pikachu/IoT-ASP/issues/61) · [#62](https://github.com/team-project-pikachu/IoT-ASP/issues/62) · [#43](https://github.com/team-project-pikachu/IoT-ASP/issues/43) · [#42](https://github.com/team-project-pikachu/IoT-ASP/issues/42) | Live URL shipped; wire backend URLs + field/e2e acceptance remain |
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
#27 secrets → #60 ADK deploy → #61 wire URLs → #62 field/e2e → #63 ruleset → #64 V&V → #65 log automation (land with this doc)
     ↘ #42 impulse/alarm (web)   ↘ #22/#26 telemetry polish   ↘ #43 specs (docs)
```

Native [#41](https://github.com/team-project-pikachu/IoT-ASP/issues/41) and parked M3–M4 / edge issues are **not** required to call web MVP done.

## Supporting MVP / continuous ship (not a separate README milestone)

| Theme | Issues | Notes |
|-------|--------|-------|
| Structured fleet logs | [#22](https://github.com/team-project-pikachu/IoT-ASP/issues/22) | [`22-structured-fleet-logs.md`](specs/22-structured-fleet-logs.md) |
| HW-limited LF / AEC `micDiff` | [#25](https://github.com/team-project-pikachu/IoT-ASP/issues/25) | [`25-hw-limited-lf-aec-micdiff.md`](specs/25-hw-limited-lf-aec-micdiff.md) |
| Colab live GCS features | [#26](https://github.com/team-project-pikachu/IoT-ASP/issues/26) | [`26-colab-live-gcs-features.md`](specs/26-colab-live-gcs-features.md); parent closed [#17](https://github.com/team-project-pikachu/IoT-ASP/issues/17) |
| Actions → Vercel secrets | [#27](https://github.com/team-project-pikachu/IoT-ASP/issues/27) | [`27-continuous-ship-dev-test-prod.md`](specs/27-continuous-ship-dev-test-prod.md) |
| ADK Cloud Run / Agent Engine | [#60](https://github.com/team-project-pikachu/IoT-ASP/issues/60) | Prod control-plane deploy (M6 ship gate) |
| Wire live backend URLs | [#61](https://github.com/team-project-pikachu/IoT-ASP/issues/61) | `BACKEND_TELEMETRY_URL` + patch URL for 3-phone fleet |
| Field acceptance + e2e | [#62](https://github.com/team-project-pikachu/IoT-ASP/issues/62) | Fleet checklist + promote Playwright |
| Main branch protection | [#63](https://github.com/team-project-pikachu/IoT-ASP/issues/63) | Ruleset / required checks |
| SEBoK V&V MVP pass | [#64](https://github.com/team-project-pikachu/IoT-ASP/issues/64) | Matrix C1–C6 / SCH1 / HOLD1 → `pass` |
| `mdc_convert` GEN_MARK guard | [#34](https://github.com/team-project-pikachu/IoT-ASP/issues/34) | Tooling |
| Impulse→blast + alarm | [#42](https://github.com/team-project-pikachu/IoT-ASP/issues/42) (canonical); dups closed | [`algorithms.md`](algorithms.md) |
| Soundcore manufacturer specs | [#43](https://github.com/team-project-pikachu/IoT-ASP/issues/43) | [`hardware/soundcore-specs.md`](hardware/soundcore-specs.md) |
| Closed-issue logging | [#68](https://github.com/team-project-pikachu/IoT-ASP/issues/68) | script + Action (PR branch under rulesets); ~~#65~~ duplicate |
| MVP roadmap doc | [#69](https://github.com/team-project-pikachu/IoT-ASP/issues/69) | this file |
## Post-MVP / research (M6–M7 + parked)

> **#60 note:** milestone label is M6, but **prod ADK deploy remains an MVP web-ship gate** (see close order above and the Supporting MVP table). Do not defer #60 as optional research.
| Milestone / lane | Issues | Notes |
|------------------|--------|-------|
| **M6** — LLM autoroute (Gemini) | [#60](https://github.com/team-project-pikachu/IoT-ASP/issues/60) **MVP deploy gate** (listed again under Supporting MVP); [#12](https://github.com/team-project-pikachu/IoT-ASP/issues/12)/[#13](https://github.com/team-project-pikachu/IoT-ASP/issues/13)/[#17](https://github.com/team-project-pikachu/IoT-ASP/issues/17) closed; [#24](https://github.com/team-project-pikachu/IoT-ASP/issues/24) ADK 2.x `parked` | [`docs/autoroute.md`](autoroute.md) |
| **M7** — Edge companions | [#14](https://github.com/team-project-pikachu/IoT-ASP/issues/14)/[#15](https://github.com/team-project-pikachu/IoT-ASP/issues/15) `parked` | C2 Pi USB-C |
| Node-3 chair / infrasound proxy | [#18](https://github.com/team-project-pikachu/IoT-ASP/issues/18) `parked` | |
| Notion hub | [#19](https://github.com/team-project-pikachu/IoT-ASP/issues/19) `parked` | |
| Sonos Beam Gen 2 sink | [#39](https://github.com/team-project-pikachu/IoT-ASP/issues/39) `parked` `research` | |
| **Vendor private study as package** | [#67](https://github.com/team-project-pikachu/IoT-ASP/issues/67) `parked` `research` | Public-safe `packages/iot-asp-study` only — see [`STUDY_PRIVATE.md`](STUDY_PRIVATE.md) |
## Status snapshot helper
Balanced stub board (may lag): [`issues/BALANCED-BUILD-STATUS.md`](issues/BALANCED-BUILD-STATUS.md).
Local issue stubs: [`issues/ISSUE-60-adk-cloud-run-deploy.md`](issues/ISSUE-60-adk-cloud-run-deploy.md) … [`ISSUE-64`](issues/ISSUE-64-sebok-vv-mvp-pass.md).
```bash
gh issue list -R team-project-pikachu/IoT-ASP --state open --limit 100
gh api repos/team-project-pikachu/IoT-ASP/milestones --jq '.[] | {title,open_issues,closed_issues}'
```
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
