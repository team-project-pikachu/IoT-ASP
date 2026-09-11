# Feature specs — index (Project 5, issues #1–#27)

One spec per Project 5 issue (or per tightly coupled group), each with the sections
Status · Goal · Shipped on `main` (cited `file:line`) · Remaining scope · Wire fields · Clamps / safety ·
Acceptance tests · CI gate · Risks / HW limits · Sources (rule: `.claude/rules/docs-and-specs.md`).
`docs/api-contract.md` is canonical for wire fields; specs link to it and never fork the tables.
`SPEC.md` (repo root) holds the Soundcore 2 manufacturer limits, the fleet topology, and a short
pointer to this index.

Board: https://github.com/orgs/team-project-pikachu/projects/5 · Status as of 2026-09-08 on branch
`claude/mdc-conversion-features-gu3yzk` (`origin/main` @ `0625e91`).

## Index

| Issue(s) | Spec | Status | Owner surface |
|----------|------|--------|---------------|
| #1 | [01-m0-public-blaster.md](01-m0-public-blaster.md) — M0 public Vercel hop blaster + telemetry fields + M0 polish | shipped (live app) + polish implemented on branch | frontend |
| #2 | [02-max-entropy-seeds.md](02-max-entropy-seeds.md) — max-entropy seeds, min hop delta, start stagger, Reseed | implemented on branch | frontend |
| #3 | [03-continuous-monitoring-watchdog.md](03-continuous-monitoring-watchdog.md) — continuous polling / monitoring watchdog | implemented on branch | frontend |
| #4 #5 #6 | [04-06-vibration-channels.md](04-06-vibration-channels.md) — physical (DeviceMotion), acoustic (mic energy), material-dependent channel selection | parked — partly shipped (`priors.MATERIAL_CHANNEL_BIAS`, vib classes); arming UI not shipped | frontend + backend |
| #7 #8 | [07-08-rlhf-loops.md](07-08-rlhf-loops.md) — RLHF +/− loops (θ vector, `localStorage` schema, bandit step) | parked — design only | frontend |
| #10 #11 | [10-11-react-rewrite.md](10-11-react-rewrite.md) — React / React Strict DOM rewrite + fleet polish | parked — constraints only | frontend |
| #14 #15 #21 #23 | [14-15-21-23-edge-integrations.md](14-15-21-23-edge-integrations.md) — Pi 5 USB-C node, Apple Home / HomeKit / Matter, Google Home Wi-Fi autorotate, AI Edge Portal | parked — research; #21/#23 docs on `main` (`docs/connectivity-wifi.md`, `docs/ai-edge-portal.md`) | infra |
| #18 | [18-node3-chair-infrasound.md](18-node3-chair-infrasound.md) — node 3 chair-taped phone + infrasound LF-accel proxy | parked — priors shipped (`infra_felt`), node not deployed | frontend + backend |
| #19 | [19-notion-hub.md](19-notion-hub.md) — Notion hub page for ASP tooling | hub created 2026-09-08; docs back-linked; optional DB/sync remaining | docs |
| #20 | [20-timestore.md](20-timestore.md) — timestore: SciPy ≥16-param fit, 0.0006 s quantum, NWS weather prior, cipher tags | implemented on `main` (`timestore.py` + `packages/algo-timestore/`, #30) | backend |
| #22 | [22-structured-fleet-logs.md](22-structured-fleet-logs.md) — structured fleet telemetry logs (`fleet_log.py`) | implemented on branch — integration hooks pending | backend |
| #24 | [24-adk-2x-migration.md](24-adk-2x-migration.md) — `google-adk` 2.x migration (`google-genai` already 2.x) | parked — keep `google-adk<2` | backend |
| #25 | [25-hw-limited-lf-aec-micdiff.md](25-hw-limited-lf-aec-micdiff.md) — HW-limited LF mic/TX + AEC, `micDiff` (`mic_diff.py`) | HW-limited — backend helper implemented on branch | backend |
| #26 | [26-colab-live-gcs-features.md](26-colab-live-gcs-features.md) — Colab live GCS: accel / gyro / `micDiff` → `meta/features` | implemented on branch (live write pending owner run) | backend |
| #27 | [27-continuous-ship-dev-test-prod.md](27-continuous-ship-dev-test-prod.md) — continuous ship: GitHub Actions dev → test → prod into Vercel | implemented on branch (secrets not yet set) | infra |
| #39 | [39-sonos-beam-sink.md](39-sonos-beam-sink.md) — Sonos Beam Gen 2 Node 3 sink | parked — ADR + AirPlay shell stub | native + research |
| #41 #48 #52 | [41-native-ios-watchos.md](41-native-ios-watchos.md) — native iOS/watchOS companion apps | stubbed — unsigned; device validation pending | native |
| #42 | [42-impulse-alarm-combined.md](42-impulse-alarm-combined.md) — combined impulse-to-blast alarm | stubbed in web + native shared logic | frontend + native |
| #43 #49 #53 | [43-soundcore-manufacturer-specs.md](43-soundcore-manufacturer-specs.md) — Soundcore 2 manufacturer dossier | documentation implemented | docs |
| #44 #46 #50 | [44-web-pwa-impulse-blast.md](44-web-pwa-impulse-blast.md) — web impulse-to-blast path | stubbed with telemetry latch | frontend |
| #45 #47 #51 | [45-web-pwa-alarm-reactivity.md](45-web-pwa-alarm-reactivity.md) — web alarm state machine | stubbed with observable clear state | frontend |
| #37 | [37-vercel-webhooks.md](37-vercel-webhooks.md) — Vercel webhooks → GitHub notify | implemented on branch (public HTTPS host + secrets owner-gated) | infra |
| #68 | [68-mvp-closed-log.md](68-mvp-closed-log.md) — closed-issue MVP log CLI + Actions | implemented on branch | infra + docs |
| #60 | [60-adk-autoroute-deploy.md](60-adk-autoroute-deploy.md) — ADK Cloud Run / Agent Engine deploy | open — service exists; prod URL owner-gated | backend |
| #61 | [61-wire-backend-urls.md](61-wire-backend-urls.md) — wire live patch/telemetry URLs for fleet | open — query-param UI; live URLs owner-gated | frontend |
| #62 | [62-mvp-field-acceptance-e2e.md](62-mvp-field-acceptance-e2e.md) — 3-phone field checklist + Playwright | checklist + local e2e; field lab pending | frontend |
| #63 | [63-main-branch-protection.md](63-main-branch-protection.md) — main ruleset / required checks | open — scripts/docs ready; apply owner-gated | infra |
| #64 | [64-sebok-vv-mvp-matrix.md](64-sebok-vv-mvp-matrix.md) — SEBoK matrix pass for MVP ship slice | open — `.vv/matrix.md` scaffold | docs |
| #65 #68 | [65-68-mvp-closed-log.md](65-68-mvp-closed-log.md) — closed-issue log CLI + Actions | implemented on branch | infra + docs |
| #69 | [69-mvp-roadmap.md](69-mvp-roadmap.md) — durable MVP milestone → issue roadmap | implemented on branch | docs |

Issues without a spec file: #9 (native SensorKit / Xcode shell — research closeout; implementation
tracked by #41 under `native/IoTASP/`), #12 #13 #16 #17 (tracking / parent items referenced from
`docs/ci.md` and spec 26).

Owner surface legend: **frontend** = `public/` (Vercel), **backend** = `services/autoroute-adk/` (GCP,
independent deploy), **infra** = `.github/`, `scripts/`, `vercel.json`, edge hardware, **docs** = `docs/`,
`reference/`, Notion.

## Known missing docs

Computed on 2026-09-08; refreshed after merging #28/#30/#31/#32 into this PR. The former "Mac-only"
doc targets below are now present on this branch / `origin/main`. Do not create placeholder copies
(`.claude/rules/docs-and-specs.md:18`).

| Target (now present) | Linked from |
|----------------------|-------------|
| `docs/materials-engineering.md` | `docs/autoroute.md` (×2), `docs/awesome-iot-asp.md` |
| `docs/mvp-tooling.md` | `docs/DESIGN_CONSTRAINTS.md`, `docs/awesome-iot-asp.md` |
| `docs/well-architected-ai.md` | `docs/awesome-iot-asp.md` |
| `docs/similar-projects.md` | `docs/awesome-iot-asp.md` |
| `docs/ux-tooling.md` | `docs/awesome-iot-asp.md` |
| `docs/ux-provenance.md` | `docs/awesome-iot-asp.md` |
| `docs/wireframe-notes.md` | `docs/awesome-iot-asp.md` |
| `docs/native-xcode.md` | `docs/awesome-iot-asp.md` |

Landed on `main` via #30/#31/#32/#28: `docs/timestore.md`, `services/autoroute-adk/iot_asp_autoroute/timestore.py`,
`packages/algo-timestore/` (#20), `docs/dependencies.md` + `.vv/deps/`, `docs/ai-edge-portal.md` (#23),
`docs/connectivity-wifi.md` (#21). The `net=wifi|cellular` telemetry tag remains optional / iOS-limited.

Links whose targets exist **on this branch** but not yet on `origin/main` (they land with this branch's PR;
listed so a link check against `main` is not misread as breakage): `docs/ci.md` → `docs/branch-protection.md`,
`docs/deploy.md`; `docs/deploy.md` → `docs/specs/27-continuous-ship-dev-test-prod.md`,
`.vv/ci/continuous-ship.md`, `.vv/deploy/VERCEL.md`; every link from this index into `docs/specs/*.md`; and the
cross-links between the spec files themselves (all of `docs/specs/` is new relative to `origin/main`).
Re-running the script after the merge should leave only the eight Mac-only rows above.

**Method** (re-run before editing this section; no network):

```bash
python3 - <<'PY'
import os, re, subprocess, pathlib
ROOT = pathlib.Path(".").resolve()
tree = set(subprocess.check_output(["git","ls-tree","-r","--name-only","origin/main"], text=True).split())
LINK = re.compile(r"\[[^\]]*\]\(([^)\s#]+\.md)(?:#[^)]*)?\)")
for md in sorted(ROOT.glob("docs/**/*.md")):
    for m in LINK.finditer(md.read_text(encoding="utf-8")):
        t = m.group(1)
        if re.match(r"^[a-z]+://", t): continue
        rel = os.path.normpath(os.path.join(md.parent.relative_to(ROOT), t))
        on_main, in_wt = rel in tree, (ROOT / rel).exists()
        if not on_main or not in_wt:
            print(f"{md.relative_to(ROOT)} -> {rel}  main={'yes' if on_main else 'NO'} worktree={'yes' if in_wt else 'NO'}")
PY
```
