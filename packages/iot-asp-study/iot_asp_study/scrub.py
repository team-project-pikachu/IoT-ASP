"""Refuse common site-PII markers in *public* package templates and docs."""

from __future__ import annotations

import re
from pathlib import Path

# Heuristics only — keep private protocol out of packages/ and docs/ on main.
_STREET_LIKE = re.compile(
    r"\b\d{3,5}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+"
    r"(?:Street|St|Court|Ct|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Way|Blvd)\b",
    re.IGNORECASE,
)
_GS_RECORDINGS = re.compile(r"gs://iot-asp-recordings-[^\s`\"']+", re.IGNORECASE)


def find_pii_markers(text: str) -> list[str]:
    """Heuristic markers for *public* trees — never encode real site strings here."""
    hits: list[str] = []
    if _STREET_LIKE.search(text):
        hits.append("street_like_address")
    if _GS_RECORDINGS.search(text):
        hits.append("private_recordings_bucket_uri")
    return hits


def scan_paths(paths: list[Path]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for p in paths:
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        hits = find_pii_markers(text)
        if hits:
            out[str(p)] = hits
    return out
