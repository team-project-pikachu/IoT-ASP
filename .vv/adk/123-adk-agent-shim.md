# V&V — #123 adk_agent shim

**Issue:** #123 — Empty `adk_agent/` directory — wire or remove  
**Slice:** Thin re-export shim + README (no Agent Engine live deploy).

## What changed

- `adk_agent/__init__.py` — re-exports `root_agent` from `iot_asp_autoroute.agent` when importable; otherwise `root_agent is None`.
- `adk_agent/README.md` — canonical path + usage.

## Gates (local-equivalent)

- No `schemaVersion` bump.
- No keys in `public/`.
- Hold/Manual and `vol_hard_max=100` untouched.
- Empty directory no longer the only occupant of `adk_agent/`.

## Not claimed

- Live Cloud Run / Agent Engine deploy (#60) still owner-gated.
- Full `google-adk` import smoke requires optional deps; dry-run path remains `services/autoroute-adk/`.
