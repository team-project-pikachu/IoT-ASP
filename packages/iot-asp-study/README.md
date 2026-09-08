# iot-asp-study (public-safe package)

Importable scaffold for **session sidecar schema**, local `study/` path resolution, and
upload helpers — without shipping site-identifying protocol from the private companion.

| Concern | Where it lives |
|---------|----------------|
| Public schema + doctor | this package (`packages/iot-asp-study`) |
| Site protocol / ethics / roster / bucket IAM | private [`IoT-ASP-study`](https://github.com/team-project-pikachu/IoT-ASP-study) + gitignored `study/` |
| Public pointer | [`docs/STUDY_PRIVATE.md`](../../docs/STUDY_PRIVATE.md) |

Tracked: GitHub **#67** (post-MVP / `parked` + `research`).

## Why not git subtree / submodule of IoT-ASP-study?

`IoT-ASP-study` is **private** and holds street addresses, recording URIs, and seat notes.
Vendoring that tree into the public default branch would leak PII. This package is a
**public-safe library** with provenance docs; operators clone the private companion
separately (or keep a local gitignored `study/`).

## Layout

```
iot_asp_study/          # library (stdlib only)
templates/              # scrubbed PROTOCOL + sidecar examples (placeholders only)
scripts/doctor.py       # path + schema + anti-PII checks
scripts/upload_recordings.sh  # requires IOT_ASP_GCS_BUCKET name (no gs://; no hardcoded private URI)
```

## Local use

```bash
# Optional: point at a private clone
export IOT_ASP_STUDY_ROOT=/path/to/IoT-ASP-study

PYTHONPATH=packages/iot-asp-study python3 -c 'from iot_asp_study import validate_sidecar; print(validate_sidecar({"node":"node1","algo":"hop","ext_source":"outside","site_code":"SITE","vib_channel":"none","started_at_utc":"2026-09-08T00:00:00Z","ended_at_utc":"2026-09-08T00:01:00Z"}))'

PYTHONPATH=packages/iot-asp-study python3 packages/iot-asp-study/scripts/doctor.py
```

Upload (shared GCS interface — bucket **name** only; script builds `gs://` internally):

```bash
export IOT_ASP_GCS_BUCKET="YOUR_PRIVATE_BUCKET"
export GOOGLE_CLOUD_PROJECT="bear-iot-asp-rec"
bash packages/iot-asp-study/scripts/upload_recordings.sh ./recordings node1
```

## Related

- Issue #67 · roadmap [`docs/mvp-roadmap.md`](../../docs/mvp-roadmap.md); private protocol stays in IoT-ASP-study
- Invariant 7 in `CLAUDE.md` — no site PII on the public branch
