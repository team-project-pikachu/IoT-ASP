# Req IDs — Issue #12 Gemini autoroute

Sources: GitHub #12 ACs, `docs/DESIGN_CONSTRAINTS.md`, `docs/api-contract.md`, `docs/autoroute.md`.

| ID | Requirement | Verify | Validate |
|----|-------------|--------|----------|
| R12-01 | Ingest → clamp → author → `meta/patches/<deviceId>.json` (`schemaVersion: 1`) | Dry-run writes patch artifact | Phone polls/applies when Hold off |
| R12-02 | `vol` is UI percent; soft==hard max **100**; legacy linear ≤1 → ×100 | Clamp unit asserts in dry-run | Slider max 100 matches contract |
| R12-03 | Band fMin/fMax ∈ [17000,23000] US (or LF [10,20] when band gated) | OOB fMin refused | Frontend clampPatch defense-in-depth |
| R12-04 | **Hold / Manual** freezes remote patch apply (frontend + backend) | author/process/`write_patch` refuse | UI Hold blocks `applyPatch`/`pollPatch` |
| R12-05 | No Gemini/Vertex API keys in public HTML | `rg` scan of `public/` | Tabs do not call Gemini directly |
| R12-06 | Backend deploy independent of Vercel; contract shared | Package + docs present | Integrate redeploy only if `public/` changed |
| R12-07 | Engine id `iot-asp-autoroute` on `bear-iot-asp-rec` | Env defaults + patch `engineId` | Org account on Chrome iOS for Enterprise |
| R12-08 | Telemetry/patch schemas aligned with api-contract | Field presence in dry-run payload | Beacon fields match table |
| R12-09 | GCS recordings layout documented (public-safe) | `docs/gcp-recordings.md` exists | Private study holds bucket IAM |
| R12-10 | Out-of-policy patch refused (algo/band/vol/duty) | Negative controls | Monitor log rationale without PII |
