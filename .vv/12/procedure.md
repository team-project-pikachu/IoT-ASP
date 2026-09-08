# Procedures — Issue #12

## V-12-A — Local dry-run (verification)

**Precondition:** Python 3 on PATH; no GCP credentials required.

```bash
cd /Users/machine/apps/IoT-ASP
bash scripts/autoroute_dev.sh
```

**Expected:**

1. Exit code `0` and banner `DRY-RUN OK`.
2. Prints `vol_hard_max=100.0`.
3. Line `clamp negatives: OK (vol 50/legacy 0.5 accept; vol 101 + OOB fMin refuse)`.
4. Line `holdManual negatives: OK (author/process/write_patch refuse)`.
5. Artifact `.autoroute-dry/meta/patches/node1.json` exists with `schemaVersion: 1`, `engineId: iot-asp-autoroute`, `vol` ≤ 100.

## V-12-B — Clamp table vs script (verification)

**Precondition:** Read `services/autoroute-adk/iot_asp_autoroute/clamps.py` `CLAMPS`.

**Expected:** `vol_soft_max == vol_hard_max == 100.0`.  
**Expected:** `scripts/autoroute_dev.sh` fallback asserts accept `vol=50` and refuse `vol=101` (no legacy “hard max 20” wording).

## V-12-C — No secrets in public HTML (verification)

```bash
rg -n 'AIza|apiKey|API_KEY|VERTEX_API|gemini.*secret' public/index.html || true
```

**Expected:** no matches. Frontend only polls patch URL / beacons telemetry.

## V-12-D — Hold / Manual wins (verification + validation sketch)

**Backend (automated in dry-run):**

1. Ingest telemetry with `holdManual: true` + `suddenFreq: true`.
2. `author_sudden_freq_patch` → refuse.
3. `process_sudden_freq` → refuse.
4. `write_patch` while latest tel has Hold → refuse.

**Frontend (manual / integrate):**

1. Open blaster; toggle **Hold / Manual** ON.
2. Confirm monitor shows hold ON; patch poll does not apply remote params.
3. Toggle OFF; poll may apply again.

## V-12-E — Docs alignment (verification)

Confirm present and cross-linked:

- `docs/api-contract.md` — `vol` 0–100; `holdManual` refuse
- `docs/gcp-recordings.md` — public-safe GCS layout
- `docs/gemini-enterprise.md` / `docs/iphone-dedicated-mode.md` — Chrome iOS active Google account = org `betty@bearresearch.io`

## V-12-F — Production 200 (integrate lane only)

```bash
curl -sS -o /dev/null -w '%{http_code}\n' https://hop-ultrasonic.vercel.app/
```

**Expected:** `200`. Not executed by GREEN lane.
