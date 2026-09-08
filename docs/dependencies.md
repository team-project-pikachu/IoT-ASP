# Dependencies — IoT-ASP

**Audit date:** 2026-09-08 (POSIX ≈ 2026-09-08T00:24Z).  
**Policy:** no `@latest`; pin ranges only; prefer patch/minor within current major; do not force majors with known breaking changes.  
**Evidence:** [`.vv/deps/`](../.vv/deps/).

## Inventory

| Surface | Manifest | Notes |
|---------|----------|-------|
| Autoroute ADK (Python) | [`services/autoroute-adk/requirements.txt`](../services/autoroute-adk/requirements.txt) | Sole `requirements*.txt` / no `pyproject.toml` |
| Public PWA | none (`public/` vanilla HTML) | No `package.json`; no CDN npm pins |
| Optional JS ADK | `@google/adk` **2.0.0** (npm; not deprecated) | Documented only in [mvp-tooling.md](mvp-tooling.md); not installed in-repo |
| Notebooks | [`notebooks/iot_asp_colab_etl.ipynb`](../notebooks/iot_asp_colab_etl.ipynb) | Imports shared `iot_asp_autoroute`; no separate pin file |
| CI | [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | `actions/checkout@v4`, `actions/setup-python@v5`, Python **3.12** |
| Timestore package | `packages/algo-timestore/` | Scaffold only; no lockfile |

## Authoritative Python pins (post-audit)

| Package | Range | PyPI latest (audit) | Resolved | Yanked / deprecated |
|---------|-------|---------------------|----------|---------------------|
| `google-adk` | `>=1.39.1,<2` | **2.8.0** | **1.39.1** | None |
| `google-genai` | `>=2.22.0,<3` | **2.22.0** | **2.22.0** | None |
| `google-cloud-storage` | `>=3.13.0,<4` | **3.13.1** | **3.13.1** | None |
| `scipy` | `>=1.14.0,<1.19` | **1.18.1** | **1.18.1** | None |
| `numpy` | `>=2.0.0,<3` | **2.5.3** | **2.5.3** | None |

### What was bumped

- `google-adk` → **`>=1.39.1,<2`** (was `>=1.0.0,<2`)
- `google-genai` → **`>=2.22.0,<3`** (was `>=1.0.0,<2`) — **required** by `google-adk>=1.36` (`google-genai>=2.9,<3`)
- `google-cloud-storage` → **`>=3.13.0,<4`** (was `>=2.14.0,<4`)
- `scipy` → **`<1.19`** (was `<1.18`, which blocked 1.18.1)
- `numpy` → **`>=2.0.0,<3`** (was `>=1.26.0`)

### What stayed (intentionally)

- **`google-adk` major 1** — Context7 `/google/adk-python` documents ADK 2.0 breaking changes. Migration tracked as **[#24](https://github.com/team-project-pikachu/IoT-ASP/issues/24)** on GitHub Project **5 (IoT-ASP)**.
- **No JS lockfile** — static `public/` only.
- **CI action majors** — `checkout@v4` / `setup-python@v5` kept (not deprecated).

### Doc note

[mvp-tooling.md](mvp-tooling.md) catalogs PyPI newest (incl. ADK **2.8.0**). **Install authority** is `requirements.txt` until #24 lands.

## SciPy / ADK API checks (Context7)

| Library ID | Check | Result |
|------------|-------|--------|
| `/scipy/scipy` | `medfilt` odd `kernel_size`; `median_abs_deviation(scale='normal')`; `find_peaks(height=, distance=)` | Stable in current docs; used by `vib_anomaly.py` |
| `/google/adk-python` | `from google.adk.agents import LlmAgent` | Present on main; **2.0 has breaking changes** vs 1.x → do not force |

## Verify commands

```bash
bash scripts/autoroute_dev.sh
bash scripts/ci_static_gates.sh
# optional: pip install -r services/autoroute-adk/requirements.txt  (venv)
```
