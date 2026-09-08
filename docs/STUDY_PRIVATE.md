# Private study package (pointer only)

Site protocol, ethics TBD, Gemini Enterprise 5-seat roster, and recording upload ops live in:

1. **Local** gitignored `study/` (never commit to the public default branch), and/or
2. Private companion repo [`team-project-pikachu/IoT-ASP-study`](https://github.com/team-project-pikachu/IoT-ASP-study).

`study/` is **gitignored** — never commit street addresses, neighbor identifiers, or recording URIs to the public default branch.

## Public-safe library (#67)

Importable scaffold (schema, path resolver, scrubbed templates, doctor):

[`packages/iot-asp-study/`](../packages/iot-asp-study/) — see its `README.md` + `PROVENANCE.md`.

```bash
export IOT_ASP_STUDY_ROOT=/path/to/IoT-ASP-study   # optional
PYTHONPATH=packages/iot-asp-study python3 packages/iot-asp-study/scripts/doctor.py
```

**History strategy:** do **not** `git subtree` / submodule the private companion into public `main` (PII). Vendor only the public-safe package; keep private git history in `IoT-ASP-study`.

Public scientific tooling (blaster PWA, ADK autoroute agent, Colab stub, literature) stays on `main`. This package is post-MVP / research (#67); it is not required for the M0–M5 public blaster.
