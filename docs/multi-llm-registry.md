# Multi-LLM autoroute registry — design sketch (#13)

**Status:** Design / clamps sketch only · **no production non-Gemini LLM calls**  
**Issue:** [team-project-pikachu/IoT-ASP#13](https://github.com/team-project-pikachu/IoT-ASP/issues/13)  
**Evidence:** [`.vv/13/`](../.vv/13/)  
**Depends on:** Gemini-only autoroute v0 stable ([#12](https://github.com/team-project-pikachu/IoT-ASP/issues/12), [adk-autoroute.md](adk-autoroute.md))

This freezes the **interface + seat-ladder** design so a future implementation issue can schedule adapters without forking the patch schema. **v0 production remains Gemini / Vertex / ADK only.**

---

## Non-negotiables

1. **Same wire contract** — all providers emit / consume [api-contract.md](api-contract.md) `schemaVersion: 1` patches and telemetry.
2. **Same safety clamps** — `services/autoroute-adk/iot_asp_autoroute/clamps.py` (`validate_patch`) is the single enforcement point before GCS write. Models never bypass clamps.
3. **Subscription-first seat ladder** — no silent spill to metered OpenRouter / raw API keys.
4. **Hold / Manual wins** — any provider path must refuse remote apply when `holdManual` is set.
5. **Frontend never embeds provider keys** — Vercel `public/` polls patches only.

---

## Registry interface (sketch)

Conceptual Python surface (not shipped). Names are illustrative.

```python
from typing import Protocol, Any

class LlmProvider(Protocol):
    id: str                    # e.g. "gemini-vertex", "copilot-sub", "hermes-pool"
    venue: str                 # "subscription" | "metered" | "offline-heuristic"
    def author_patch(self, telemetry: dict[str, Any], priors: dict[str, Any]) -> dict[str, Any]:
        """Return raw patch dict. Must not write GCS."""
        ...

class LlmRegistry:
    def __init__(self, allowlist: list[str], primary: str = "gemini-vertex"): ...
    def resolve(self, intent: str = "autoroute") -> LlmProvider: ...
    def author_clamped(self, telemetry: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        """resolve → author_patch → validate_patch → (ok, msg, clamped)."""
        ...
```

### Adapter allowlist (future)

| Provider id | Venue | Role | Prod v0 |
|-------------|-------|------|---------|
| `gemini-vertex` / ADK `iot-asp-autoroute` | subscription (Gemini Enterprise seats) | **Primary** author | **Only live path** |
| `offline-heuristic` | offline | `sudden_freq.author_sudden_freq_patch` dry-run / fallback | Allowed (no LLM) |
| `copilot-sub` / `copilot-ent` | subscription seat | Optional secondary | **Parked** |
| `hermes-pool` (Nous) | subscription | Optional secondary | **Parked** |
| `openrouter` / raw Anthropic·OpenAI keys | **metered** | Escape hatch only | **Forbidden** unless `ALLOW_METERED_TIER=1` elected |

Do **not** call Copilot / Nous / OpenRouter from production Cloud Run / Agent Engine until this issue is un-parked and a new implementation ticket is scheduled.

---

## Seat / cost ladder

Align with house trial ladder intent (subscription before metered):

```text
gemini-vertex (Enterprise seats)
    → optional copilot-ent / copilot-sub   [parked]
    → optional hermes-pool                [parked]
    → openrouter / raw keys               [metered — explicit opt-in only]
```

| Rule | Detail |
|------|--------|
| Primary | One Gemini Enterprise seat drives continuous monitor ([gemini-enterprise.md](gemini-enterprise.md)) — Safari tabs do **not** each call Gemini |
| Advance | Only on **capacity / credit exhaustion** of the current venue — never because a scored sample was `0.0` |
| Metered | Require explicit env opt-in (`ALLOW_METERED_TIER=1` or equivalent) + human election in issue comment |
| Telemetry | Log `providerId` + `venue` on patch rationale / meta (no secrets) |

---

## Clamp ownership (unchanged)

Regardless of which `LlmProvider.author_patch` runs:

| Gate | Owner |
|------|-------|
| Band / vol / pulse / shriek / algo whitelist | `clamps.validate_patch` |
| Hold refuse | `sudden_freq` / tools before write |
| GCS write | `tools.write_patch` after clamp OK |
| Schema | `schemaVersion: 1` |

Negative controls for a future impl ticket: bad provider JSON rejected; metered provider refused when opt-in unset; Hold blocks write.

---

## Close criteria (design sketch)

- [x] Registry interface sketch documented
- [x] Seat/cost ladder subscription-first
- [x] Explicit “no production non-Gemini” clamp
- [x] Same schema + `validate_patch` ownership stated
- [x] Evidence package under `.vv/13/`

**Implementation** stays future work (new issue or un-park #13). Project board Done is owned by the **integrate** lane; may wait on #12 evidence-green if the board gate is joint.

## Related

- [autoroute.md](autoroute.md) — control loop
- [adk-autoroute.md](adk-autoroute.md) — Gemini ADK package
- [api-contract.md](api-contract.md) — wire schema
- [gemini-enterprise.md](gemini-enterprise.md) — 5-seat roster template
