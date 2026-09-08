# Provenance — IoT-ASP-study integration

| Field | Value |
|-------|--------|
| Companion (private) | https://github.com/team-project-pikachu/IoT-ASP-study |
| Public package | `packages/iot-asp-study` in https://github.com/team-project-pikachu/IoT-ASP |
| Strategy | **Vendored public-safe scaffold** (not `git subtree`, not submodule) |
| Rationale | Companion contains site-identifying protocol; public default branch must stay scrubbed (`docs/STUDY_PRIVATE.md`, gitignored `study/`) |
| History | Private git history stays in `IoT-ASP-study`. This package is new public code with templates derived from **structure only** (placeholders). |
| Issue | #67 |

Do not reintroduce private `study/*.md` content into this tree.
