# M0 field acceptance — 3-phone Soundcore fleet (#62)

Ship gate for the public web blaster (`public/index.html` → hop-ultrasonic on Vercel).  
**Constraint source:** [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) (C1–C6).  
**Issue tracker stub:** [issues/ISSUE-62-mvp-field-acceptance-e2e.md](issues/ISSUE-62-mvp-field-acceptance-e2e.md)  
**Evidence pack:** [../.vv/62/](../.vv/62/)

Safari (or Chrome iOS) + **native A2DP only** — no Web Bluetooth TX.

## Fleet setup

| Item | Expectation |
|------|-------------|
| Phones | 3 × iPhone (or equivalent) on continuous **120 V AC** (C5); Low Power Mode off |
| Speakers | 3 × Soundcore 2 (or equivalent), each AC-charged |
| Pairing | Phone *n* ↔ speaker *n* via **Settings → Bluetooth** (C1); 1:1 only |
| App | Production hop-ultrasonic URL **or** local `python3 -m http.server` of `public/` |
| Backend | Optional `?patch=` / `?telemetry=` (#61) — skip if URLs unset |

## Checklist (tick in lab; copy outcomes into `.vv/62/FIELD-PASS.md`)

### C1 — A2DP route

- [ ] **FA-01** Each phone’s system audio route is the paired Soundcore (Control Center / Now Playing), not speakerphone-only.
- [ ] **FA-02** Confirm no in-app Bluetooth picker / `navigator.bluetooth` TX path is used.

### C3 — SDD surface + Signal on / incoherent hops

- [ ] **FA-03** Open the PWA on phones 1/2/3; Mode Blaster/TX; **Signal on**.
- [ ] **FA-04** Hops are **incoherent** across phones (independent seeds / fleet seed compare shows incoherent OK or distinct seeds).

### HOLD1 / C4 — Hold/Manual + gain honesty

- [ ] **FA-05** **Hold / Manual** freezes remote patch apply; releasing resumes poll apply.
- [ ] **FA-06** Vol path can sit at 100% UI; absolute SPL still limited by BT + Soundcore DSP (honesty banner visible).

### suddenFreq

- [ ] **FA-07** With autorotate on, observe `suddenFreq` / `suddenState` progress (**onset → rotate**) in telemetry panel or Copy fleet_log JSONL.

### Night curve honesty (C5-aware)

- [ ] **FA-08** Outside **22:00–07:00 America/New_York**, `nightNY` inactive (or documented user override).
- [ ] **FA-09** Inside that window, night curve affects vol target **without** inventing battery-duty caps.

### C6 + Soundcore roll-off (#43)

- [ ] **FA-10** Default band stays **17–23 kHz** on A2DP; LF 10–20 Hz remains gated / `na` on Soundcore path.
- [ ] **FA-11** **Soundcore 2 ultrasonic warning** visible in UI; Systems check row notes BassUp/DSP near-ultrasonic roll-off.

### Telemetry / secrets

- [ ] **FA-12** Copy fleet_log JSONL → keys align with Python `RECORD_KEYS` (#22).
- [ ] **FA-13** Optional live `#61` URLs: beacons/polls succeed; skip if unset.
- [ ] **FA-14** No API keys in page source / Network (env **names** only).

## Local / CI Playwright (not a substitute for FA-01…FA-11)

```bash
make e2e   # bash tests/e2e/run.sh — headless Chromium vs public/
```

Headless Chromium **cannot** prove Safari A2DP or Soundcore SPL. It gates Hold/Manual, telemetry schema, reseed, watchdog, fleet sim, Soundcore warning presence, and suddenFreq controls.

## CI decision (#62 AC) — **informative waiver (M0)**

| Job | Ruleset | Rationale |
|-----|---------|-----------|
| `e2e smoke` | **Not required** — remain in `tests/test_ruleset_json.py` non-required allowlist `{"e2e smoke"}` | Browser cache / install cost + headless≠Safari A2DP; promotion to required is owned by **#63** after owner election |

Docs stay in sync: [ci.md](ci.md), [branch-protection.md](branch-protection.md). Do **not** edit `.github/rulesets/main-protection.json` for #62 alone.

## Closing this issue

1. Complete one dated field pass in [`.vv/62/FIELD-PASS.md`](../.vv/62/FIELD-PASS.md).
2. Ensure `make e2e` / CI `e2e smoke` is green on the merge SHA (informative OK).
3. Append closed-log via [#65](https://github.com/team-project-pikachu/IoT-ASP/issues/65) / `scripts/mvp_closed_log_append.sh`.
