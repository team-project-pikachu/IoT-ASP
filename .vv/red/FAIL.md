# RED team FAIL — IoT-ASP SEBoK V&V adversarial audit

| Field | Value |
|-------|--------|
| **Audit UTC** | `2026-09-08T00:13:22Z` |
| **Revision** | `e41c3c0e76ef9e0d9ddb59995cc7faf769a8bb79` (`e41c3c0`) |
| **Plan** | `~/.cursor/plans/iot-asp_sebok_e2e_a0905e55.plan.md` |
| **Repo** | `/Users/machine/apps/IoT-ASP` |
| **Scope** | Tree vs SEBoK V&V + `DESIGN_CONSTRAINTS` C1–C6 + `api-contract` — **no implementation** |
| **Verdict** | **FAIL** — do not promote Project 5 Todos to Done |

Companion: [PASS.md](PASS.md) (partial greens only). Re-audit after greens if tree changes.

---

## SEBoK promotion blockers (summary)

| Gate | Status |
|------|--------|
| Requirements capture → evidence under `.vv/<issue>/` | **FAIL** — no `.vv/12|16|17|9|13/`, no `docs/vv/`, no `.vv/matrix.md` |
| Verification (schema/clamps/dry-run/tests) | **FAIL** — dry-run OK path exists but negative controls stale/skipped; **zero** unit/integration tests |
| Validation (Hold/Manual, no keys in HTML, live ingest) | **FAIL** — main frontend script **does not parse**; live ingest URL empty; Hold contract mismatch |
| Negative controls | **FAIL** — package dry-run never asserts `vol > hard_max` refusal; fallback asserts contradict `vol_hard_max=100` |
| Issue #12 / #16 / #17 evidence packages | **FAIL** |

---

## F1 — CRITICAL: frontend script SyntaxError (Hold / telemetry / patch dead)

**Finding:** Duplicate `const` redeclaration aborts the entire IIFE. Node syntax check:

```text
SyntaxError: Identifier 'telSensOrient' has already been declared
```

| File:line | Detail |
|-----------|--------|
| `public/index.html:494` | `const telSensOrient = …, telSensLight = …` |
| `public/index.html:497` | **same identifiers redeclared** |

**Impact:** Hold/Manual (`holdPatchBtn` listeners ~1741–1747), `applyPatch` / `pollPatch`, `beaconTelemetry`, band gates, Systems check — **none execute**. HTML chrome exists; behavior claimed for C3/C4 Hold and #12 frontend is unverifiable in-browser.

**SEBoK:** Validation fail for Hold blocks apply; verification fail for deployable frontend.

---

## F2 — CRITICAL: `vol_hard_max` vs dry-run negative asserts (stale / skipped)

| File:line | Detail |
|-----------|--------|
| `services/autoroute-adk/iot_asp_autoroute/clamps.py:19–21` | `vol_soft_max` = `vol_hard_max` = **100.0** (C4) |
| `services/autoroute-adk/iot_asp_autoroute/clamps.py:96–97` | Refuse only when `vol > 100` |
| `scripts/autoroute_dev.sh:12–14` | If `iot_asp_autoroute.dry_run` imports, script **exits 0** — **never runs** fallback asserts |
| `scripts/autoroute_dev.sh:61–63` | Fallback: `validate_patch(… vol: 50 …); assert not ok` — comment claims “hard max 20” |

**Observed (revision `e41c3c0`):** `vol=50` → `ok=True`. Fallback assert is **false under current clamps**. Happy-path dry-run prints `DRY-RUN OK` with `vol: 100.0` and skips the negative control entirely.

**SEBoK:** Verification negative control “bad patch rejected” is **not executed** on the default path; fallback path would **fail** or encode wrong policy.

---

## F3 — CRITICAL: #12 live ingest gaps

| File:line | Detail |
|-----------|--------|
| `public/index.html:460–462` | `BACKEND_BASE_URL` / `BACKEND_PATCH_URL` / `BACKEND_TELEMETRY_URL` all `""` |
| `public/index.html:549–551` | Empty telemetry → no beacon target offline |
| `services/autoroute-adk/ingest_main.py:1–3,16–49` | “Optional HTTP ingest **stub**”; no deploy manifest / URL in-repo |
| `docs/api-contract.md:17–20` | Live override via `?telemetry=` / constants — production defaults still mock-only |
| Plan lane `exec-12-autoroute` | Requires ingest → clamp → author → patch + evidence `.vv/12/` |

**Observed:** `https://hop-ultrasonic.vercel.app/` → HTTP **200**, but serves static mock `public/patch.json` only. No Cloud Run ingest URL, no `.vv/12/` procedure/result. Continuous monitor e2e is **docs + local dry mirror**, not live GCP loop.

---

## F4 — HIGH: priors not scored (#16)

Plan: wire priors into autoroute + vib→algo **weights**; verify prior **coefficients** in worker path; validate nonsense prior ignored.

| File:line | Detail |
|-----------|--------|
| `services/autoroute-adk/iot_asp_autoroute/priors.py:5–31` | String blurbs only; `prior_text` concatenates prose — **no scores/weights/coefficients** |
| `services/autoroute-adk/iot_asp_autoroute/tools.py:76–78` | `seismo_acoustic_priors()` → `{text, keys}` only |
| `services/autoroute-adk/iot_asp_autoroute/sudden_freq.py:45–59,99–104` | Routing via `vibClass` string table; `priors` field is **label list** + `priorNotes` text |
| `docs/physics.md:14–37` | Equations documented; no numeric prior vector |

**Negative control gap:** `prior_text(["nonsense_xyz"])` → `''` (silent ignore) — no assert, no score floor, no “nonsense prior ignored” test artifact under `.vv/16/`.

---

## F5 — HIGH: Colab pipeline stub (#17)

| File:line | Detail |
|-----------|--------|
| `notebooks/iot_asp_colab_etl.ipynb` | **2 cells**: markdown stub + `print("Stub — wire GCS + STFT in Colab")` |
| `docs/colab-gemini-pipeline.md:18–24` | Claims notebook does auth, STFT, vib features, `meta/features/` writes |
| `notebooks/iot_asp_colab_etl.md:4–46` | Richer sketch in **.md** — **not** what the `.ipynb` executes |

**SEBoK:** Doc/notebook divergence; cannot verify offline dry cells or feature columns vs telemetry contract from the actual notebook.

---

## F6 — HIGH: missing automated tests

| Evidence | Detail |
|----------|--------|
| Repo search | **0** `tests/`, `test_*.py`, `*_test.py`, jest/pytest harnesses |
| Plan verify bullets | “clamp unit checks”, synthetic vib fixtures, Hold negative controls |

Dry-run scripts (`dry_run.py`, `dry_run_anomaly.py`, `autoroute_dev.sh`) are demos, not a regression suite with exit-on-assert for Hold / OOB freq / secrets / nonsense priors.

---

## F7 — HIGH: Hold / Manual vs api-contract + backend write path

| File:line | Detail |
|-----------|--------|
| `docs/api-contract.md:23` | Hold freezes **remote** apply; **local suddenFreq rotate may continue** |
| `public/index.html:743–744` | `autorotateOnSudden`: `if (!suddenAuto \|\| holdManual) return` — Hold also blocks **local** rotate (stricter than contract; moot while F1 breaks JS) |
| `docs/api-contract.md:90` | `holdManual` true → **backend must refuse patches** |
| `services/autoroute-adk/iot_asp_autoroute/sudden_freq.py:33–34,67–68` | Author / `is_sudden_freq_event` respect Hold |
| `services/autoroute-adk/iot_asp_autoroute/tools.py:37–62` | `write_patch` **does not** read latest telemetry `holdManual` — ADK can write clamped patch while Hold is on |

**Observed:** `write_patch("node1", …)` with Hold-only telemetry still returns `ok=True`. Agent prompt (`agent.py:37`) is soft policy, not enforcement.

---

## F8 — MEDIUM: frontend ↔ backend clamp divergence (defense-in-depth)

| Field | Frontend `clampPatch` | Backend `CLAMPS` / `validate_patch` |
|-------|----------------------|-------------------------------------|
| `pulseMs` | `public/index.html:1670` → **40–220** | `clamps.py:22` → **20–200** |
| `shriekMs` | `:1671` → **30–120** | `:23` → **20–120** |
| `vibThreshold` | `:1672` → **0.02–0.8** | `:24` → **0.01–2.0** |

Phone can accept/apply values backend would reject (or vice versa) if JS were live — contract says backend is authoritative (`api-contract.md:138–140`).

---

## F9 — MEDIUM: SEBoK scaffolding absent

| Expected (plan §1) | Observed |
|--------------------|----------|
| `docs/vv/README.md` | **missing** |
| `.vv/matrix.md` | **missing** |
| `.vv/12/`, `.vv/16/`, `.vv/17/`, `.vv/9/`, `.vv/13/` | **missing** |
| `.firecrawl/developer-index/INDEX.md` | directory empty / **no INDEX.md** |
| `.gitignore` | `.vv` **not** ignored — audits may leak into commits unless careful |

---

## F10 — MEDIUM: C6 / safety tool incomplete; soft clamp dead

| File:line | Detail |
|-----------|--------|
| `tools.py:71` | `band_hz: [17000, 23000]` only — LF **10–20** (C6) not exposed in `list_safety_clamps` |
| `clamps.py:98–101` | Soft-clamp branch unreachable while soft==hard==100 |

---

## F11 — LOW: telemetry contract gaps

| Gap | Detail |
|-----|--------|
| `materialPreset` | In `api-contract.md:54` example; **absent** from `telemetryPayload()` (`index.html:1607–1643`) |
| `public/patch.json` | Mock ok; no `priors` / `band` fields vs full patch schema |

---

## Focus checklist (requested)

| Focus | Result |
|-------|--------|
| Hold/Manual | **FAIL** — F1 (JS dead) + F7 (contract/local rotate + `write_patch` bypass) |
| `vol_hard_max` vs dry-run asserts | **FAIL** — F2 |
| Secrets in HTML | See PASS (no keys found); constants empty by design |
| Missing tests | **FAIL** — F6 |
| #12 live ingest gaps | **FAIL** — F3 |
| Priors not scored | **FAIL** — F4 |
| Colab stub | **FAIL** — F5 |

---

## Promotion decision

**Refuse Done** on #12 / #16 / #17 until: (1) F1 fixed and re-verified in browser, (2) dry-run negative controls aligned to `vol_hard_max=100` and always executed, (3) live ingest URL + `.vv/12` evidence, (4) prior coefficients or explicit “text-only priors” AC rewrite + tests, (5) real Colab notebook cells matching docs, (6) SEBoK matrix + per-issue evidence packages.

*No Project board updates performed (per RED charter).*
