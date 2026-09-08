# Similar projects (`gh search`) — adapt vs rewrite

Verified 2026-09-07. Prefer MIT/Apache/BSD/CC0.

| Project | Stars | License | Adapt for IoT-ASP |
|---------|------:|---------|-------------------|
| [ggerganov/ggwave](https://github.com/ggerganov/ggwave) | ~7.8k | MIT | Data-over-sound codecs — **reference only**; we keep custom near-US hop/FSK |
| [quiet/quiet](https://github.com/quiet/quiet) | ~1.7k | BSD-3 | Acoustic modem ideas; rewrite for 17–23 kHz + Safari |
| [quiet/QuietModemKit](https://github.com/quiet/QuietModemKit) | ~0.5k | BSD-3 | iOS native path notes for future Xcode shell |
| [google/adk-python](https://github.com/google/adk-python) | ~21k | Apache-2.0 | **Primary** ADK runtime for autoroute |
| [google/adk-samples](https://github.com/google/adk-samples) | ~10k | Apache-2.0 | Agent packaging patterns |
| [mdn/webaudio-examples](https://github.com/mdn/webaudio-examples) | ~1.4k | CC0 | UX/analyser patterns ([ux-provenance.md](ux-provenance.md)) |
| [GoogleChromeLabs/web-audio-samples](https://github.com/GoogleChromeLabs/web-audio-samples) | ~0.7k | Apache-2.0 | Web Audio samples |
| [minipief/pyva](https://github.com/minipief/pyva) | ~36 | MIT | Vibroacoustics toolbox — Colab/offline priors, not on-phone |
| [killercrush/music-tempo](https://github.com/killercrush/music-tempo) | — | (check) | Onset / spectral ideas for `suddenFreq` |

## Adapt vs rewrite (MVP)

| Keep / adapt | Rewrite ourselves |
|--------------|-------------------|
| ADK agent structure from google/adk-* | Sudden-freq → Gemini noise autorotate loop |
| Web Audio analyser habits from MDN/Chrome Labs | 17–23 kHz hop/pulse/shriek + A2DP-only TX |
| ggwave/quiet as literature | Safari PWA fleet + patch.json clamps |

No huge clones this pass. Connectivity: [DESIGN_CONSTRAINTS.md](DESIGN_CONSTRAINTS.md).
