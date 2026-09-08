# MVP tooling — verified libraries

**Pull date:** 2026-09-07; **install audit:** 2026-09-08 — see [dependencies.md](dependencies.md). Packages verified via PyPI / npm / Context7 (`/google/adk-python`, `/websites/adk_dev`, `/googleapis/python-genai`). **Do not invent package names.**

Formal constraints: [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md) — **native A2DP only** for phone TX; **no Web Bluetooth** dependency for MVP audio out.

| Layer | Library / tool | Why | Install / pin |
|-------|----------------|-----|----------------|
| Public web | Vanilla HTML + Web Audio API | Static Vercel PWA; Safari field nodes | (none — browser APIs) |
| BT audio out | **iOS system A2DP** | OS route to Soundcore; not a JS lib | Pair in Settings |
| Web Bluetooth | **Not used (MVP TX)** | Constraint C1 | — |
| Sudden-freq detect | AnalyserNode spectral flux / peak jump | Local heuristic + telemetry `suddenFreq` | in `public/index.html` |
| ADK agent | `google-adk` **1.39.1** install (`<2`); PyPI latest **2.8.0** parked [#24](https://github.com/team-project-pikachu/IoT-ASP/issues/24); optional `@google/adk` **2.0.0** (npm) | Gemini autoroute patch author | `pip install -r services/autoroute-adk/requirements.txt` |
| Gemini / Vertex | `google-genai` **2.22.0** | Enterprise / Vertex client | same requirements.txt |
| GCS | `google-cloud-storage` **3.13.1** | Telemetry + patches + recordings | same requirements.txt |
| Colab ETL | `google.colab` + `gsutil` / GCS client | Spectra / vib features | Colab runtime |
| Deploy | Vercel CLI / static `public/` | Public site (other agent owns SSO) | `vercel` |
| UX authoring | Chrome DevTools + Lighthouse + axe-core | Desktop Chrome for design iteration | see [ux-tooling.md](ux-tooling.md) |
| Materials priors | Docs + literature (no CFD lib on phone) | Channel bias by mount class | [materials-engineering.md](materials-engineering.md) |

## Context7 IDs

| ID | Use |
|----|-----|
| `/google/adk-python` | ADK install, `LlmAgent`, deploy |
| `/websites/adk_dev` | ADK docs portal |
| `/googleapis/python-genai` | `genai.Client`, Vertex |
| `/googleapis/python-storage` | GCS blobs |

## Anti-patterns

- Adding `navigator.bluetooth` for Soundcore TX
- Metered Vertex keys in git
- Inventing npm names like `google-adk` (use `@google/adk` or Python `google-adk`)
