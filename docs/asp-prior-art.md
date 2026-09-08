# ASP prior art (awesome-list · government · USPTO · Firecrawl · Context7)

**Rule:** [.cursor/rules/asp-prior-art.mdc](../.cursor/rules/asp-prior-art.mdc) (alwaysApply for IoT-ASP algo/docs).  
Supersedes the shorter awesome-list-only note; keep [awesome-list-asp.md](awesome-list-asp.md) as a pointer.

## Mandate

Before greenfield ASP algorithms, search and fetch:

1. **Awesome lists** — https://github.com/topics/awesome-list via `gh`
2. **Government / open scientific** — NIST, NASA NTRS, arXiv, .gov acoustics/DSP, FCC as relevant
3. **USPTO** — patents/prior art for ultrasonics / vibrometry / signal processing; cite lineage; novel derivatives only (no claim copy-paste)

## Firecrawl (service)

Prefer workspace Firecrawl **CLI stable** (`firecrawl_stable.sh` / `firecrawl-cli-stable`) — `developer` for library/API/bug index, `search`/`scrape`/`map` for hubs and .gov. Prefer CLI over MCP per research-cli-kit. Cache under `.firecrawl/`. **Do not invent costs** — report `creditsUsed` only when the JSON provides it.

### Durable developer index (Phase 1)

- Index: [`.firecrawl/developer-index/INDEX.md`](../.firecrawl/developer-index/INDEX.md) (**71** unique `id` entries this wave)
- Machine list: `.firecrawl/developer-index/entries.json`
- Awesome hubs scraped: `readme:faroit/awesome-python-scientific-audio`, `readme:nitnelav/awesome-acoustic`
- .gov / NTRS search caches: `.firecrawl/search_-20260908T001251Z.json` (NIST; `creditsUsed=2`), `.firecrawl/search_-20260908T001252Z.json` (NASA NTRS; `creditsUsed=2`)

Quoted developer-index examples:

- `web:https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html` — “Welch's method computes an estimate of the power spectral density by dividing the data into overlapping segments…”
- `web:https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html` — “Use non-linear least squares to fit a function, f, to data…”
- `readme:faroit/awesome-python-scientific-audio` — scientific audio / DSP Python lineage for ASP adoption

## Context7

For SciPy, ADK, Web Audio, and other SDKs: `resolve-library-id` → `query-docs` **one concept per call** (CLI `context7_stable.sh`; MCP fallback when CLI docs empty). Prefer Context7 over memory for API syntax.

| Library ID | Concept | Cache |
|------------|---------|-------|
| `/scipy/scipy` | `scipy.signal.welch` PSD | `.context7/docs-_scipy_scipy-scipy.signal.welch_power_spectral_density_.md` |
| `/scipy/scipy` | `scipy.optimize.curve_fit` | `.context7/docs-_scipy_scipy-scipy.optimize.curve_fit_nonlinear_least_squares_.md` |
| `/google/adk-python` | `LlmAgent` / `root_agent` / `adk deploy agent_engine` | `.context7/docs-_google_adk-python-LlmAgent_root_agent_tools_deploy_Agent_Engine_.md` |
| `/websites/webaudio_github_io_web-audio-api` | `AudioContext` / Oscillator / Gain | `.context7/docs-_websites_webaudio_github_io_web-audio-api-AudioContext_createOscillator_GainNode_.md` |

Cited contracts (MCP `query-docs` / official docs):

- **SciPy welch** — `scaling` `'density'` vs `'spectrum'`; returns `(f, Pxx)`; `nfft >= nperseg`
- **ADK** — `root_agent = LlmAgent(..., tools=[...])`; deploy via `adk deploy agent_engine`
- **Web Audio** — `AudioContext` graph; `OscillatorNode` / `GainNode`; `connect()` wiring (gesture-unlock + max gain path under C1/C4)

## SEBoK V&V

Requirements ↔ issues ↔ evidence: [vv/README.md](vv/README.md) · [`.vv/matrix.md`](../.vv/matrix.md).

## Known drift (later lanes)

- `scripts/autoroute_dev.sh` still asserts old vol refuse vs `clamps.py` `vol_hard_max=100`
- Missing `docs/gcp-recordings.md`

## Outstanding

Unfinished prior-art / adoption shards → Issues → [Project 5](https://github.com/orgs/team-project-pikachu/projects/5).

## Privacy

No street addresses or study-site PII in public citations.
