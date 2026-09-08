# UX provenance — adapt, don’t invent

Patterns adapted from mature permissive OSS. No new design system from scratch.

| Source | License | Stars (approx) | What we adapt |
|--------|---------|----------------|---------------|
| [mdn/webaudio-examples](https://github.com/mdn/webaudio-examples) | CC0-1.0 | ~1.4k | Analyser / oscillator demo structure; spectrum readout habits |
| [GoogleChromeLabs/web-audio-samples](https://github.com/GoogleChromeLabs/web-audio-samples) | Apache-2.0 | ~0.7k | Sample project layout; Web Audio best practices |
| [Tonejs/Tone.js](https://github.com/Tonejs/Tone.js) | MIT | ~14k | Timing/scheduling concepts only — **not** required MVP dependency |
| Existing `public/index.html` | project | — | Dark scientific panel, SF stack, Hold/Manual, monitor grid |

**Avoid copying:** GPL-only UI shells (e.g. Tonejs/ui) into the public app without license review.

Firecrawl map/search receipts: `reference/knowledge-base/raw/fc-map-*.json`, `fc-search-webaudio-ui.json`.

Wireframes: [wireframe-notes.md](wireframe-notes.md). Constraints: native A2DP only for TX ([DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md)).
