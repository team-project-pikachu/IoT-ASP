# Dependency audit evidence — 2026-09-08

**POSIX audit:** ≈ 2026-09-08T00:24Z–00:28Z  
**Project:** GitHub Project 5 (IoT-ASP)  
**Parked major:** [#24](https://github.com/team-project-pikachu/IoT-ASP/issues/24) — `google-adk` 2.x

## Inventory

- Python: `services/autoroute-adk/requirements.txt` only (no `pyproject.toml`)
- JS: no `package.json`; npm `@google/adk@2.0.0` documented only (not deprecated)
- Notebooks: share ADK package path; no separate pins
- CI: `.github/workflows/ci.yml` → Python 3.12, `checkout@v4`, `setup-python@v5`

## PyPI (no yank / no Deprecated classifier on targets)

| Package | Before range | After range | Resolved |
|---------|--------------|-------------|----------|
| google-adk | `>=1.0.0,<2` | `>=1.39.1,<2` | **1.39.1** |
| google-genai | `>=1.0.0,<2` | `>=2.22.0,<3` | **2.22.0** |
| google-cloud-storage | `>=2.14.0,<4` | `>=3.13.0,<4` | **3.13.1** |
| scipy | `>=1.14.0,<1.18` | `>=1.14.0,<1.19` | **1.18.1** |
| numpy | `>=1.26.0,<3` | `>=2.0.0,<3` | **2.5.3** |

## Why genai major 2 landed (ADK 1.x still)

`google-adk==1.39.1` requires `google-genai>=2.9,<3`. Keeping genai on major 1 with ADK ≥1.36 is **ResolutionImpossible**.

## Why ADK major 2 did **not** land

Context7 `/google/adk-python`: ADK 2.0 breaking changes (agent API / events / sessions). Tracked in #24.

## Verify

| Gate | Exit |
|------|------|
| `bash scripts/autoroute_dev.sh` | **0** |
| `bash scripts/ci_static_gates.sh` | **0** |
| CI clamp + Hold import smoke | **OK** |
| `LlmAgent` import (ADK 1.39.1) | **OK** |
| SciPy `medfilt` / MAD / `find_peaks` | **OK** (1.18.1) |

## Artifacts

- `pip-dry-run-2026-09-08.txt` — first successful resolver dry-run (`Would install … google-adk-1.39.1 … google-genai-2.22.0 …`)
- `resolved-2026-09-08.txt` — installed versions in audit venv
- `pip-report-2026-09-08.json` — empty `install[]` after satisfy (exit 0); use dry-run txt + resolved txt
- Canonical doc: [`docs/dependencies.md`](../../docs/dependencies.md)

**Dry-run exit:** `0` (requirements resolve + `autoroute_dev.sh` + `ci_static_gates.sh`).
