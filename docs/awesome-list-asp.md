# Awesome-list → ASP algorithm base

**Canonical rule:** [.cursor/rules/asp-prior-art.mdc](../.cursor/rules/asp-prior-art.mdc)  
**Full process:** [asp-prior-art.md](asp-prior-art.md) (awesome + government + USPTO + Firecrawl + Context7).

## Mandate (summary)

Always look for pre-existing projects via [GitHub topic `awesome-list`](https://github.com/topics/awesome-list) before inventing greenfield ASP packages. Also search government sites and USPTO; fetch with **Firecrawl**; pull library docs with **Context7**.

## How agents search

```bash
gh search repos --topic awesome-list signal OR acoustics OR dsp --limit 10
gh search repos --topic awesome scipy signal --limit 10
# then Firecrawl scrape/search on chosen URLs; Context7 for SciPy/ADK/Web Audio APIs
```

## Adopted / cited (living)

| Source | Use in ASP |
|--------|------------|
| [awesome-list topic](https://github.com/topics/awesome-list) | Discovery hub |
| SciPy (via Context7 `/scipy/scipy`) | Vib anomaly + nonlinear timestore (`welch` / `curve_fit`) |
| Google ADK (`/google/adk-python`) | Autoroute `LlmAgent` / Agent Engine deploy |
| Web Audio (`/websites/webaudio_github_io_web-audio-api`) | `AudioContext` hop / gain graph |
| [faroit/awesome-python-scientific-audio](https://github.com/faroit/awesome-python-scientific-audio) | DSP / scientific audio priors |
| [nitnelav/awesome-acoustic](https://github.com/nitnelav/awesome-acoustic) | Acoustics awesome list |
| Firecrawl developer-index | [`.firecrawl/developer-index/INDEX.md`](../.firecrawl/developer-index/INDEX.md) (71 entries) |
| [awesome-iot-asp.md](awesome-iot-asp.md) | Redirect → [README.md](README.md) (canonical index) |

## Outstanding

→ [Project 5](https://github.com/orgs/team-project-pikachu/projects/5)
