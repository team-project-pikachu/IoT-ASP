# IoT-ASP — Claude Code project memory

Near-ultrasonic **hop fleet**: three iPhones, each blasting 17–23 kHz carriers through its own
Soundcore 2 over **iOS native Bluetooth A2DP**, with a decoupled GCP/ADK "autoroute" control plane
that authors clamped parameter patches from telemetry. Public scientific tooling; **no site PII**.

Live app: https://hop-ultrasonic-1digital-design.vercel.app/ (source mirror: `public/`).
Board: https://github.com/orgs/team-project-pikachu/projects/5 — issues `#1`–`#27`, milestones M0–M5.

## Layout

```
public/                          # static PWA blaster (Vercel) — single-file app: index.html + patch.json mock
services/autoroute-adk/          # Google ADK Python agent + tools + clamps + priors + Colab ETL (GCP, independent deploy)
packages/iot-asp-study/          # public-safe templates/schema/doctor (#67); gitignored study/ unchanged
scripts/                         # gates + dry-run + KB refresh + mdc converter
tests/                           # pytest (stdlib + numpy/scipy) — run before every push
docs/                            # contract, constraints, autoroute, CI, physics, specs/
docs/specs/                      # one spec per Project 5 issue (goal, wire, clamps, acceptance, CI gate)
reference/                       # literature + Firecrawl/Context7 knowledge digests
.github/workflows/               # ci.yml (breaking-change gates), deploy.yml (dev → test → prod)
.claude/rules/                   # path-scoped rules (paths: frontmatter); generated + hand-written
.cursor/rules/*.mdc              # Cursor rules (local) → converted by scripts/mdc_convert.py
.vv/                             # verification evidence packages (CI, deploy, sensors)
```

## Non-negotiable invariants (CI enforces most of these)

1. **C1 — phone → speaker is iOS native A2DP only.** Never Web Bluetooth, BLE GATT, or an in-page
   device picker for the carrier path (`docs/DESIGN_CONSTRAINTS.md`).
2. **C2 — Raspberry Pi field node is USB-C and parked (#14).** Not in the web MVP.
3. **Frontend only polls/applies patches and beacons telemetry.** No Gemini/Vertex keys, ADK code, or
   Vertex clients in `public/`. `scripts/ci_static_gates.sh` greps for key patterns.
4. **Wire contract is `schemaVersion: 1`** (`docs/api-contract.md`). Additive fields are fine; a breaking
   change bumps `schemaVersion` in `clamps.py`, `public/index.html`, `public/patch.json`, and the doc.
5. **Clamps:** `vol_hard_max == vol_soft_max == 100.0` (UI percent; legacy linear ≤ 1 is ×100).
   `fMin`/`fMax` ∈ [17000, 23000] for band `17-23k`; LF band `10-20` only when `lfDriveCapable` is true.
   `pulseMs` 20–200, `shriekMs` 20–120, `vibThreshold` 0.01–2.0, `algo` ∈ whitelist. Refuse, never silently rewrite, out-of-policy values (except the documented soft vol clamp).
6. **Hold / Manual wins.** `holdManual: true` in telemetry means the backend refuses to author or write
   patches and the phone ignores remote patches. The UI label `Hold / Manual`, wire key `holdManual`, and
   element `holdPatchBtn` must stay in `public/index.html`.
7. **No site PII** anywhere public: no street addresses, neighbor identifiers, recording URIs, speech
   transcripts. Study material lives in gitignored `study/`; public templates live in `packages/iot-asp-study`.
8. **Physics honesty:** linearized acoustics / Navier–Stokes / seismo-acoustic coupling are priors and
   prompt constraints only. Never claim CFD on-phone. Safari + BT cannot capture or play true infrasound;
   LF accelerometer energy is a felt proxy.
9. **No fabricated citations.** Literature IDs come from `reference/LITERATURE.md` and `priors.py`.
10. **Secrets by name only** (`GOOGLE_CLOUD_PROJECT`, `IOT_ASP_GCS_BUCKET`, `VERCEL_TOKEN`, …). Values live
    in 1Password Environment `dev`, GitHub Actions secrets, Colab `userdata`, or Secret Manager. Never in git, chat, or issues.
11. **Backend and frontend deploy independently.** ADK/Cloud Run changes never require a Vercel redeploy
    unless `public/` changed, and vice versa.

Known drift to keep in mind (do not "fix" silently — it is a product decision):
`docs/api-contract.md` still describes vol "soft ≤12, hard refuse >20" while `clamps.py` is 100/100 and
the phone-side defensive clamp `VOL_PATCH_MAX` in `public/index.html` is 12 with a slider max of 60.

## Commands

```bash
bash scripts/ci_static_gates.sh          # Hold/Manual, no keys, patch.json schemaVersion, clamp constants
bash scripts/autoroute_dev.sh            # offline dry-run: suddenFreq → clamped patch under .autoroute-dry/
python3 -m pytest tests -q               # unit tests (needs numpy scipy pytest; pip install -r requirements-dev.txt)
python3 scripts/mdc_convert.py           # .cursor/rules/*.mdc → CLAUDE.md blocks + .claude/rules + .claude/skills
python3 scripts/mdc_convert.py --check   # CI: fail if converted outputs are stale
make gates test mdc                      # same three, via Makefile
bash scripts/kb_refresh.sh               # Context7 knowledge-base refresh (needs context7_stable.sh wrapper)
```

Toolchain: Python 3.11+ (3.12 in CI), stdlib-first. `google-adk` is optional for dry-run
(`iot_asp_autoroute/__init__.py` soft-fails the agent import). `numpy`/`scipy` are required by
`vib_anomaly.py`, which `tools.py` imports.

## Wire contract cheat-sheet (`schemaVersion: 1`)

- Telemetry heartbeat ★: `schemaVersion`, `deviceId`, `ts`, `algo` (wire names: `hop | am_gate |
  shriek_chirp | shriek_sweep | burst | infra_mod`), `suddenFreq`. Optional: `peakHz`, `absA`/`a`,
  `micEnergy`, `vibClass` (`none | physical | acoustic | infra_felt`), `holdManual`, `band`, `power`,
  `nightNY`, `lfArmed`, `lfDriveCapable`, `materialPreset`, `vol`, `pulseMs`, `shriekMs`, `vibThreshold`.
- Patch ★: `schemaVersion`, `algo`. Optional: `fMin`, `fMax`, `vol`, `pulseMs`, `shriekMs`, `vibThreshold`,
  `seedAction` (`keep | reseed`), `rationale`, `engineId`, `trigger`, `nodeId`, `band`, `priors`.
- UI aliases: `pulse` ↔ `am_gate`, `shriek` ↔ `shriek_chirp`. Backend always emits wire names.
- Storage: `meta/telemetry/<deviceId>/<ts>.json`, `meta/patches/<deviceId>.json`,
  `meta/features/<deviceId>/…` (Colab/ETL, never authoritative), `meta/logs/<deviceId>/<date>.jsonl`.

## Working conventions

- **Prior-art check before building anything.** Search, in this order, and record the result in the spec's
  "Prior art" section: (1) this repo (`rg`, `git log -S`, all `origin/*` branches); (2) the owner's Mac clone
  state described in the GitHub issues (it is usually ahead of `origin/main`); (3) the org's other repos;
  (4) awesome-lists at https://github.com/topics/awesome-list (awesome-claude-code, awesome-cursorrules,
  awesome-actions, awesome-vercel, awesome-observability); (5) Context7 / Firecrawl developer search for an
  OSS tool or official integration. Reuse or adapt when a maintained tool fits; build only when it does not,
  and say why (dependency policy, determinism, missing semantics). Register: `docs/PRIOR_ART.md`.
- **Branches:** `claude/<topic>-<id>` for Claude sessions; Cursor works on the owner's Mac clone at
  `/Users/machine/apps/IoT-ASP`. Expect the Mac to be ahead of `origin/main`; keep edits additive and in
  clearly delimited blocks to minimise merge conflicts.
- **PRs must reference an issue** (`Fixes #N`, `Closes #N`, `Related: #N`) — `pr_issue_ref` CI job fails
  otherwise. Use `.github/PULL_REQUEST_TEMPLATE.md`.
- **Before pushing:** all three commands above green, plus `python3 scripts/mdc_convert.py --check`.
- **Evidence:** substantive changes add or refresh a `.vv/<area>/*.md` evidence file (what ran, exit codes, URIs; no secrets).
- **Docs:** every feature has a spec in `docs/specs/`; `SPEC.md` is the manufacturer/fleet spec plus an index of feature specs.
- **Commits:** imperative subject ≤ 72 chars; body says what and why; no model identifiers in commits or PR bodies.

## Cursor ↔ Claude Code rules interop

Cursor project rules are `.cursor/rules/*.mdc` (YAML frontmatter `description`, `globs`, `alwaysApply`).
`scripts/mdc_convert.py` maps them deterministically:

| `alwaysApply` | `globs` | `description` | Cursor type | Claude Code target |
|---|---|---|---|---|
| `true` | any | any | Always | managed block in this file (between `<!-- mdc:begin … -->` / `<!-- mdc:end … -->`) |
| `false` | set | any | Auto Attached | `.claude/rules/<name>.md` with `paths:` = globs |
| `false` | unset | set | Agent Requested | `.claude/skills/<name>/SKILL.md` (`name`, `description`) |
| `false` | unset | unset | Manual (`@rule`) | `.claude/skills/<name>/SKILL.md` (invoke with `/<name>`) |

Rules named in `.mdc-convert.json` under `"spec"` are routed into `SPEC.md` managed blocks instead.
Edit the `.mdc` source, not the generated output; re-run the converter. Hand-written text outside the
markers is preserved.

<!-- mdc:managed-section -->

<!-- mdc:begin asp-backend-vv-ci source=.cursor/rules/asp-backend-vv-ci.mdc sha256=b1a76b52e0f3 -->
### IoT-ASP backend decoupling, SEBoK V&V evidence, CI gates, Project 5 tracking

# ASP backend / V&V / CI (locked)

## Backend decoupled from Vercel

- Static app (`public/`) only **polls/applies patches** and optionally **beacons telemetry**.
- Never embed Gemini/Vertex keys, ADK agent code, or Vertex clients in frontend HTML/JS.
- ADK stack (`services/autoroute-adk/`) deploys independently (Agent Engine / Cloud Run) — **ADK deploy without Vercel**.
- Wire contract: `docs/api-contract.md` with **`schemaVersion`**. Prefer additive fields; bump `schemaVersion` only on breaking wire changes.
- Clamps (vol ≤100 UI %, band freqs, algo whitelist, Hold refuse) enforced on **backend** before write; frontend applies defensively.

## SEBoK V&V

- Verification/validation evidence lives under **`.vv/`** (per-issue packages + matrix when present).
- **Hold / Manual wins** over remote patches; include negative controls (bad patch rejected, Hold refuse, nonsense priors ignored).
- Do not promote Project work to Done without fresh evidence for the exact revision under test.
- Parser/dry-run demos alone are not promotion proof when the contract defines a semantic result.

## CI + change control

- GitHub Actions on **PRs linked to issues**.
- **MVP non-breaking → ship continuously** (CI green on `main` → Actions Deploy preview then prod). **Breaking → Project 5 issue first** (no silent `schemaVersion` / clamp / C1–C6 breaks).
- **Agents: commit incremental MVP slices** as each non-breaking slice finishes and local sim is green (`bash scripts/autoroute_dev.sh` + `bash scripts/ci_static_gates.sh`) — open/update an issue-linked PR; do **not** leave large uncommitted working trees.
- Deploy workflow: `.github/workflows/deploy.yml` (requires `VERCEL_TOKEN` / `VERCEL_ORG_ID` / `VERCEL_PROJECT_ID`; skips clearly if missing — see `docs/ci.md`). Never skip Hold/clamp/schema gates.
- Outstanding locked work → issues on `team-project-pikachu/IoT-ASP` → [Project 5](https://github.com/orgs/team-project-pikachu/projects/5).

## Account + privacy (docs / CI artifacts)

- Public docs: org **`betty@bearresearch.io`** for GCP/Gemini/Chrome iOS context when an account must be named.
- No secrets, `.env`, API keys, or street addresses in repo, CI logs, or `.vv/` narratives.

## Agent must not

- Couple frontend redeploy to ADK redeploy as a hard dependency.
- Skip `.vv/` evidence or negative controls when claiming V&V pass.
- Merge breaking API/contract changes without `schemaVersion` / issue linkage.
<!-- mdc:end asp-backend-vv-ci -->

<!-- mdc:begin asp-ops-fleet-control source=.cursor/rules/asp-ops-fleet-control.mdc sha256=9c06f6b4db61 -->
### IoT-ASP locked ops/fleet/control — SDD app, A2DP, loudness, Chrome iOS, night, power, privacy

# ASP ops / fleet / control (locked)

Public scientific tooling. **No street PII** in public IoT-ASP. Prefer org account **`betty@bearresearch.io`** for Chrome iOS / GCP / Gemini in public docs (not personal Gmail).

## Control surface (SDD via app)

- The **public web app** is the software-defined driving surface (`discover → model → plan → execute`).
- Humans + Gemini/ADK patches drive the acoustic plant; speaker hardware knobs alone are not the control plane.
- **Hold / Manual wins** over remote `/patch.json`. Local Signal / sensors may stay armed.
- Detail: `docs/sdd-app-control.md`, `docs/DESIGN_CONSTRAINTS.md` (C3).

## Audio path (non-negotiable)

| Rule | Detail |
|------|--------|
| TX | **Native iOS Bluetooth A2DP** only (Settings + Control Center). **Not** Web Bluetooth TX. |
| Loudness | Max practical Web Audio (default / clamp **100%** UI). Utilize Soundcore **~12 W** dual drivers via OS A2DP. Be honest: BT absolute volume + speaker DSP still limit SPL. |
| Autorotate | **Hardware-limited** — respect A2DP/AAC/SBC + BassUp/DSP roll-off; do not claim flat ultrasonic FR. |
| Bands | Public TX **17–23 kHz only** (10–20 Hz UI removed). Sink: Sonos Beam Gen 2 via OS audio; Night Sound/Speech/Loudness OFF for clean max. |

## Chrome iOS + dedicated phone

- On **Signal on / Arm sensors**: arm every available sensor (Web Audio unlock, mic, DeviceMotion, DeviceOrientation; Ambient Light if present). Document WebKit limits — do not invent Safari APIs.
- Dedicated fleet phone: wake lock / keep awake when practical; Guided Access or Focus checklist; maximize CPU/RAM within WebKit; **Low Power Mode off**.
- Detail: `docs/sensors-chrome-ios.md`, `docs/iphone-dedicated-mode.md`, `docs/iphone-bluetooth.md`.

## Fleet power + night + connectivity

- **Continuous 120 V AC** for study path (phones + speakers charging). No battery duty-cycle assumptions in autoroute gain/dwell.
- Night window **22:00–07:00 America/New_York**: volume **0 → 100%** in **0.5** glides/jumps (schedule/courtesy only — not battery-save).
- Connectivity: **Google Home Wi‑Fi now**; cellular later (track as Project issue). Tag power `ac120` in telemetry when known.

## Parked / deferred

- **AI Edge Portal**: optional later when installed/allowlisted — do not block MVP (`docs/ai-edge-portal.md`).
- Outstanding locked work → GitHub issues on `team-project-pikachu/IoT-ASP` → [Project 5](https://github.com/orgs/team-project-pikachu/projects/5).

## Agent must not

- Add Web Bluetooth TX, site street addresses, or battery-save logic that contradicts C5.
- Soften max-gain defaults to “neighbor-safe” without an explicit user election separate from Hold.
<!-- mdc:end asp-ops-fleet-control -->

<!-- mdc:begin asp-prior-art source=.cursor/rules/asp-prior-art.mdc sha256=79dd2af2b97c -->
### ASP prior art — awesome-list, .gov, USPTO; fetch via Firecrawl; libs via Context7
_globs: packages/**/*, services/autoroute-adk/**/*, docs/**/*, public/index.html, reference/**_

# ASP prior art + Firecrawl + Context7 (IoT-ASP)

Before inventing new Adaptive Signal Processing algorithm packages (timestore, SciPy anomaly, autoroute, hop/Soundcore path), **search priors** and **fetch with Firecrawl / Context7** — do not greenfield when an awesome-listed, government, or patent lineage already fits.

Rule index for related locked decisions: [docs/rules-index.md](../../docs/rules-index.md).

## 1. Awesome lists (`gh`)

- In-repo hubs first: `docs/awesome-list-asp.md`, `docs/awesome-iot-asp.md`
- Topic hub: https://github.com/topics/awesome-list
- Related: `awesome`, `awesome-list`, `awesome-python`, acoustics/DSP domain lists
- Prefer Firecrawl **developer-index** / search skills to inventory listed tools before greenfield
- CLI:
  - `gh search repos --topic awesome-list <keywords>`
  - `gh search repos --topic awesome <keywords>`

## 2. Government + open scientific sources

Search and cite (no street-address PII):

| Source | Use |
|--------|-----|
| NIST | Metrology, DSP, acoustics standards |
| NASA NTRS | Acoustics / vibration / signal methods |
| arXiv | Open scientific priors (cite DOI/arXiv id) |
| .gov acoustics/DSP | Agency technical pages |
| FCC | Spectrum / RF adjacency when relevant |

## 3. USPTO prior art

- Search patents/public applications for signal processing, ultrasonics, vibrometry, acoustic sensing.
- Design **novel derivatives** that **cite priors**; **do not copy claims verbatim**.
- Document lineage in `docs/` and/or `reference/`.

## 4. Firecrawl (mandatory fetch path)

Use **Firecrawl as a service** to retrieve awesome-list READMEs, .gov pages, USPTO/public patent pages, and related blogs — prefer workspace **CLI stable** over inventing scrapers:

- Skills: `firecrawl-cli-stable`, `firecrawl-search`, scrape/map/crawl as appropriate
- Prefer `scripts/*_stable.sh` / research-cli-kit **CLI before MCP** when the prefer-cli rule applies
- Cache under project `.firecrawl/` when used
- **Do not invent Firecrawl dollar costs** — report credits/tokens only when files provide them
- Cite scraped URLs in docs

## 5. Context7 (mandatory for library/SDK docs)

When incorporating SciPy, Google ADK, Web Audio, or other libraries into the ASP base:

1. `resolve-library-id` (CLI stable or MCP)
2. `query-docs` scoped to one concept per call
- Prefer Context7 over training-memory for API syntax
- Workspace: `context7-cli-stable` / MCP `plugin-context7-context7` / `user-Context7`
- Prefer CLI (`context7_stable.sh`) when research-cli-kit requires it

## 6. Prefer incorporate → cite → file gaps

1. Prefer incorporation over greenfield when a prior fits formal constraints (native BT A2DP, Hold/Manual, schemaVersion).
2. Cite awesome / .gov / USPTO / Firecrawl URLs and Context7 library ids in `docs/` (see [docs/asp-prior-art.md](../../docs/asp-prior-art.md)).
3. Outstanding gaps → GitHub issues on `team-project-pikachu/IoT-ASP` → [Project 5](https://github.com/orgs/team-project-pikachu/projects/5).

## Out of scope

- No secrets or site PII in public docs.
- No verbatim patent claim text as product code.
- Do not break C1 native Bluetooth / SDD app control constraints.
<!-- mdc:end asp-prior-art -->
