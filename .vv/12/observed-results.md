# Observed results — Issue #12 (2026-09-08)

## V-12-A Dry-run

| Check | Result |
|-------|--------|
| Exit code | `0` |
| `vol_hard_max` printed | `100.0` |
| Clamp negatives | OK |
| Hold/Manual negatives | OK |
| Patch written | `.autoroute-dry/meta/patches/node1.json` |
| `schemaVersion` | `1` |
| `engineId` | `iot-asp-autoroute` |
| Authored `vol` | `100.0` |
| Trigger path | `suddenFreq` → `burst` (physical vib prior weights) |

Command:

```text
bash scripts/autoroute_dev.sh
→ DRY-RUN OK
```

## V-12-B Clamp / script drift

| Check | Result |
|-------|--------|
| `CLAMPS["vol_hard_max"]` | `100.0` |
| `autoroute_dev.sh` fallback assert | Accepts vol 50 + legacy 0.5→50; refuses vol 101 (fixed former “hard max 20” drift) |

## V-12-C Public HTML secrets

| Check | Result |
|-------|--------|
| Gemini/API key patterns in `public/index.html` | **none** |
| Personal Gmail in public `docs/` / `public/` / `services/` | **none** |

## V-12-D Hold / Manual

| Layer | Result |
|-------|--------|
| `author_sudden_freq_patch` + hold | refuse (`holdManual — refuse patch`) |
| `process_sudden_freq` + hold | refuse |
| `write_patch` with latest tel hold | refuse |
| Frontend `applyPatch` / `pollPatch` | early-return when `holdManual` (code review; UX smoke = integrate) |

## V-12-E Docs

| Doc | Result |
|-----|--------|
| `docs/gcp-recordings.md` | **created** (public-safe) |
| `docs/api-contract.md` | linked gcp-recordings; vol ≤100 |
| `docs/gemini-enterprise.md` | Chrome iOS → org `betty@bearresearch.io` |
| `docs/iphone-dedicated-mode.md` | org account + Hold wins |
| Private `IoT-ASP-study/study/PROTOCOL.md` | Chrome iOS prefer org account (no personal Gmail listed in public) |

## V-12-F Production

| Check | Result |
|-------|--------|
| Vercel HTTP 200 | **held for integrate lane** |

## Pass/fail summary

| Req | Status |
|-----|--------|
| R12-01 … R12-05, R12-07 … R12-10 | **PASS** (local) |
| R12-06 deploy independence | **PASS** (docs + package; live ADK deploy N/A this lane) |
| Production validation | **DEFER** integrate |
| Project board Done | **DEFER** integrate |
