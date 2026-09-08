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
   transcripts. Study material lives in gitignored `study/`.
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
