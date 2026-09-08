# Gemini acoustic event detector (stub)

Python stub for M8 sound-burst + glass-shatter classification.

```bash
python3 services/gemini-burst-detect/detect.py
```

Returns JSON-shaped dict: `{burst, eventClass, confidence, escalateDb}`.

Live Gemini Enterprise / Vertex: owner enables APIs via `scripts/home_apis_gcloud_bootstrap.sh --apply` after confirmation. Secret names only in 1Password `dev`.
