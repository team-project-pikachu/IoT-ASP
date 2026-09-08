# Cursor rules index (IoT-ASP)

Durable agent rules under [`.cursor/rules/`](../.cursor/rules/). Human design narrative remains in [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md). **No street PII.**

| Rule | Apply | Captures |
|------|--------|----------|
| [asp-ops-fleet-control.mdc](../.cursor/rules/asp-ops-fleet-control.mdc) | alwaysApply | SDD via app; max Web Audio / ~12 W; native A2DP (not Web Bluetooth TX); Chrome iOS sensor arm; hardware-limited autorotate; night 22:00–07:00 ET @ 0.5 steps; Google Home Wi‑Fi → cellular later; dedicated iPhone; bands 17–23 kHz (+ gated 10–20 Hz); 120 V AC; org account; AI Edge Portal parked; Project 5; no public street PII |
| [asp-algo-telemetry.mdc](../.cursor/rules/asp-algo-telemetry.mdc) | globs (docs algo/api, `public/`, ADK, packages, scripts) | Awesome-list → Firecrawl → Context7 before greenfield; structured JSON telemetry; 24 h + year timestore; quantum 0.0006; ≥16-param SciPy + ciphers + Fairfax weather; anomaly 1 Hz / vib 0.0005 backend-only |
| [asp-backend-vv-ci.mdc](../.cursor/rules/asp-backend-vv-ci.mdc) | alwaysApply | `schemaVersion` API contract; ADK without Vercel; SEBoK evidence in `.vv/`; Hold/Manual + negative controls; GH Actions on PRs linked to issues; **MVP non-breaking → continuous ship** (`deploy.yml`); breaking → Project 5 first |
| [asp-prior-art.mdc](../.cursor/rules/asp-prior-art.mdc) | alwaysApply + globs | Awesome-list / .gov / USPTO priors; Firecrawl fetch; Context7 libs; novel derivatives; gaps → Project 5 |

## Related docs (not rules)

- [sdd-app-control.md](sdd-app-control.md) · [power-fleet.md](power-fleet.md) · [iphone-dedicated-mode.md](iphone-dedicated-mode.md)
- [api-contract.md](api-contract.md) · [algorithms.md](algorithms.md) · [timestore.md](timestore.md)
- [asp-prior-art.md](asp-prior-art.md) · [ai-edge-portal.md](ai-edge-portal.md)
