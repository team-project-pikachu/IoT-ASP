# #7 / #8 — RLHF positive / negative reinforcement loops (θ vector, localStorage schema, bandit step)

Issues: https://github.com/team-project-pikachu/IoT-ASP/issues/7 · https://github.com/team-project-pikachu/IoT-ASP/issues/8 · Milestone: M4 — RLHF +/- reinforcement loops · Labels: `enhancement`, `parked`
Related: [02-max-entropy-seeds.md](02-max-entropy-seeds.md) (`reseed`, `MIN_HOP_DELTA_HZ`), [04-06-vibration-channels.md](04-06-vibration-channels.md) (`vibThreshold`), [22-structured-fleet-logs.md](22-structured-fleet-logs.md) (log records).

## Status

**Parked — design only.** Nothing RLHF-shaped exists on `origin/main`: no reward buttons, no θ vector,
no reward key on the wire. This spec fixes the policy-parameter vector θ, the `localStorage` schema, the
update rule for `r = +1` (#7) and `r = −1` (#8), and the clamps that bound every update, so that both
loops share one implementation when unparked. "RLHF" here is literal: a **human** taps *good* / *bad*;
the "policy" is the phone's local hop scheduler, not an LLM. No model training happens anywhere.

## Goal

1. **#7 positive:** human taps **good / reward** (or a future automatic signal: strong SNR, successful
   decode) → `r = +1` → reinforce the current hop policy parameters θ (dwell band, vib threshold, seed-mix
   weight, frequency-coverage prior).
2. **#8 negative:** human taps **bad / punish** (or failed decode / clipping) → `r = −1` → penalise:
   push a reseed, widen jumps, raise vib sensitivity.
3. Persist θ and the reward history in `localStorage` under a versioned JSON schema that can later be
   synced (telemetry or Colab) without a breaking change.
4. Every update is a **bounded bandit step**: θ never leaves the phone clamps, never touches `vol`,
   and never overrides Hold / Manual or a remote patch's band.

## Shipped on `main`

Verified by reading `origin/main` @ `0625e91`:

| What | Where |
|------|-------|
| Local persisted state uses `localStorage` keys `hop.deviceId`, `hop.seed`, `hop.algo`, `hop.vibAuto`, `hop.suddenAuto`, `hop.role` | `public/index.html:496-503`, `:634`, `:652`, `:681`, `:1472` |
| Per-device PRNG `mulberry32(seed)` and `pickFreq` / `pickDwell` (uniform in band, independent dwell) | `public/index.html:523-543` (spec 02 cites) |
| `vibSens` slider (1–40 → `vibThreshold = value/10`) | `public/index.html:329`, `:1356` |
| Remote patch may `reseed` (`seedAction: "reseed"`) and set `vibThreshold`, `pulseMs`, `shriekMs`, `fMin`/`fMax` — all clamped by `clampPatch` | `public/index.html:1375-1420` |
| Hold / Manual short-circuits `applyPatch` | `public/index.html:1391` |
| Backend `seedAction` ∈ `keep \| reseed`; patch clamps (`pulseMs` 20–200, `shriekMs` 20–120, `vibThreshold` 0.01–2.0, band 17–23 kHz) | `docs/api-contract.md:123-135`; `services/autoroute-adk/iot_asp_autoroute/clamps.py:19-25` |
| No reward / RLHF key anywhere (`grep -rn "reward\|rlhf" public docs services` → nothing on `origin/main`) | — |
| Spec 02 (branch) adds `entropySeed()`, `reseed(reason)`, `MIN_HOP_DELTA_HZ`, and the `seedSource` indicator that this design reuses | `docs/specs/02-max-entropy-seeds.md` § Remaining scope |

## Remaining scope

Phone-only, one block `// ══ rlhf loops (#7 #8) ══` in `public/index.html`; no backend change is required
for v1 (the backend may later read the optional telemetry fields below).

### θ — policy parameter vector (v1, 8 scalars + 6 bins)

| Key | Meaning | Range (clamp) | Default |
|-----|---------|---------------|---------|
| `dwellLo`, `dwellHi` | hop dwell bounds (s) | `[0.05, 2.0]`, `dwellLo < dwellHi` | current `dwellLo()/dwellHi()` |
| `minDeltaHz` | minimum hop delta multiplier on `MIN_HOP_DELTA_HZ()` | `[0.5, 3.0]` | `1.0` |
| `vibThreshold` | same quantity the slider exposes | `[0.02, 0.8]` (phone clamp) | slider/10 |
| `seedMix` | probability that a shake / negative reward triggers `reseed` | `[0.0, 1.0]` | `0.25` |
| `pulseBias`, `shriekBias` | additive ms offsets applied when the local scheduler picks pulse / shriek | `[-20, 20]`, `[-15, 15]` | `0` |
| `coverage[6]` | frequency-coverage prior: weights of six equal sub-bands between `bandLow()` and `bandHigh()` | each `[0.25, 4.0]`, renormalised to mean 1 | `[1,1,1,1,1,1]` |

`pickFreq` (spec 02) samples the sub-band index from `coverage` (weighted) and then uniform inside it —
the RNG stream stays seed-determined. `vol` is **not** in θ (residential gain is a human decision).

### `localStorage` schema — key `hop.rlhf` (JSON)

```json
{
  "schemaVersion": 1,
  "theta": { "dwellLo": 0.12, "dwellHi": 0.9, "minDeltaHz": 1.0, "vibThreshold": 0.15,
             "seedMix": 0.25, "pulseBias": 0, "shriekBias": 0, "coverage": [1,1,1,1,1,1] },
  "arms":  { "hop": {"n": 3, "q": 0.33}, "pulse": {"n": 1, "q": -1.0}, "shriek": {"n": 0, "q": 0.0} },
  "n": 4, "nPlus": 3, "nMinus": 1,
  "last": { "r": 1, "ts": "2026-09-08T00:00:00Z", "algo": "hop", "reason": "ui" },
  "updatedAt": "2026-09-08T00:00:00Z"
}
```

`schemaVersion` is the local schema (independent of the wire's `schemaVersion: 1`); unknown keys are
ignored on load; a parse failure resets to defaults and logs `rlhf reset`.

### Update rule (one function `rewardStep(r, reason)`, r ∈ {+1, −1})

Two-level bandit, deterministic given the current state:

1. **Arm value (algo choice):** `q[a] ← q[a] + α·(r − q[a])` with `α = 1 / min(n[a]+1, 20)` for the
   algo `a` active at tap time (UI alias `hop | pulse | shriek`). The local vib router
   (`routeFromVib`) becomes ε-greedy over `q` with `ε = 0.15`: with probability 1−ε pick the best arm among
   those the vib class allows, else the existing random choice.
2. **Parameter nudge (step η = 0.1, then clamp to the table above):**
   - `r = +1` (#7): move θ toward the *current* observed values — `dwellLo/Hi` toward the dwell that just
     played, `coverage[bin(lastTarget)] *= 1 + η`, `vibThreshold` unchanged, `seedMix *= 1 − η`.
   - `r = −1` (#8): `coverage[bin(lastTarget)] *= 1 − η`; `minDeltaHz *= 1 + 2η` (wider jumps);
     `vibThreshold *= 1 − η` (higher sensitivity); `seedMix = min(1, seedMix + 2η)` and, with
     probability `seedMix`, call `reseed("rlhf")` immediately (spec 02 reschedules).
3. Renormalise `coverage` to mean 1; persist; `monLog("rlhf r=±1", "rlhf", {r, algo, theta}, "info")`
   (structured log, spec 22 shape; no PII).

Buttons `#rewardGoodBtn` / `#rewardBadBtn` sit next to *Reseed*; a *Reset learning* link clears
`hop.rlhf`. Automatic rewards (SNR, decode, clipping) are **out of scope** for v1; the hook is
`rewardStep(r, "auto:<signal>")`.

## Wire fields

None required for v1. Proposed **optional, additive** telemetry fields for a later sync — not yet in
`docs/api-contract.md`, listed here so the name is agreed before any phone emits them:

| Field | Type | Notes |
|-------|------|-------|
| `reward` | `-1 \| 0 \| 1` | last human reward since the previous heartbeat (0 = none) |
| `rewardN` | number | total rewards this session (`nPlus + nMinus`) |

Adding them is an integration request against `docs/api-contract.md` (integrator-owned). θ itself is
never sent — it is device policy, not a metric; Colab/ETL may receive it later via `meta/features/`,
never via `meta/patches/`.

## Clamps / safety

- Every θ component is clamped to the table above **after** each step; the phone's `clampPatch` bounds
  (`vibThreshold` 0.02–0.8, `pulseMs` 40–220, `shriekMs` 30–120 at `index.html:1383-1385`) remain the
  outer envelope for anything θ feeds into the scheduler.
- `vol` is never touched by a reward. Band (`fMin`/`fMax`) is never touched; `coverage` only reweights
  inside the current band, so the 17–23 kHz clamp holds by construction.
- **Hold / Manual wins:** `rewardStep` still records the reward and updates `q`/θ (a human tap is a
  local action) but does **not** call `reseed` or reschedule while `holdManual` is true.
- Remote patches keep precedence: `applyPatch` values overwrite θ-derived scheduler inputs for that patch
  cycle; θ resumes from the patched values (they are within clamps by definition).
- Learning is per device (`localStorage`); no shared or global policy, consistent with "no shared seed".
- No PII: rewards, timestamps, algo names and numeric θ only. No free text is stored.

## Acceptance tests

Static (`tests/test_public_html.py`, additive, once the block lands):

1. `function rewardStep(` present exactly once; both `"rewardGoodBtn"` and `"rewardBadBtn"` ids present.
2. `"hop.rlhf"` literal present; `schemaVersion: 1` inside the rlhf default object (assert the block text
   contains `theta:` and `coverage:`).
3. The rlhf block does not contain `vol.value` or `fMin.value` writes (grep the block text between
   `// ══ rlhf loops (#7 #8) ══` and the next `// ══`).

Deterministic unit checks via the debug hook (`window.__hop.getState()`, spec 01) in
`tests/e2e/public_smoke.spec.mjs`:

4. Fresh context → `getState().rlhf.n === 0`, `theta` equals defaults.
5. Click `#rewardBadBtn` twice → `theta.minDeltaHz` increased (`> 1.0`), `theta.vibThreshold < 0.15`,
   `nMinus === 2`, and `localStorage["hop.rlhf"]` parses with `schemaVersion === 1`.
6. Click `#rewardGoodBtn` once → `nPlus === 1`, `arms[<current algo>].q > 0`.
7. With Hold / Manual on, `#rewardBadBtn` does not change `seed` (no reseed under Hold).
8. Corrupt `localStorage["hop.rlhf"] = "{"`, reload → defaults restored, log record `event: "rlhf reset"`.
9. 200 alternating rewards keep every θ component inside its range (property check in `page.evaluate`).

## CI gate

- `tests` job (static assertions) blocks; the e2e checks run in spec 01's optional Playwright lane.
- `static_gates` unchanged. No backend gate until the optional wire fields land in `api-contract.md`.

## Risks / HW limits

- Human reward is sparse and noisy; with `α = 1/min(n+1, 20)` the arm values converge slowly on purpose
  so one accidental tap cannot flip the router.
- `localStorage` can be cleared by iOS (storage pressure, private mode); learning is best-effort and the
  page must run correctly with no stored value (spec 02 rule for `hop.seed` applies).
- Rewarding the *scheduler* cannot compensate for the A2DP codec roll-off (`SPEC.md`): a "good" tap
  reinforces what survived the Bluetooth path, which is a property of the speaker, not of θ.
- BT latency means the sound a human judges may be 100–300 ms behind the scheduler state stamped in `last`.

## Sources

- GitHub issues #7, #8 (read via the GitHub connector, 2026-09-08): θ contents ("dwell band, vib threshold,
  seed mix weights, frequency coverage prior"), `localStorage` + JSON schema, "r=+1 REINFORCE/bandit step",
  "push reseed / wider jumps / higher vib sensitivity" for r=−1.
- Update rule is the standard incremental sample-average / ε-greedy bandit form (Sutton & Barto,
  *Reinforcement Learning: An Introduction*, 2nd ed., §2.4–2.5, http://incompleteideas.net/book/the-book-2nd.html).
- Repo: `docs/specs/02-max-entropy-seeds.md` (reseed / min delta), `docs/api-contract.md` (`seedAction`,
  clamps), `public/index.html` (`origin/main` @ `0625e91`, lines cited), `.claude/rules/public-frontend.md`.
