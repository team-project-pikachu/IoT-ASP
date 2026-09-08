"""Refuse common site-PII markers in *public* package templates and docs."""

from __future__ import annotations

import re
from pathlib import Path

# Heuristics only — keep private protocol out of packages/ and docs/ on main.
# Address range includes 1–2 digit street numbers (e.g. "12 Main Street").
_STREET_LIKE = re.compile(
    r"\b\d{1,5}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+"
    r"(?:Street|St|Court|Ct|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Way|Blvd)\b",
    re.IGNORECASE,
)
# Any non-placeholder gs:// URI is private material in the public package.
# Require an alphanumeric bucket start so prose / bash `${var#gs://}` do not match.
_GS_URI = re.compile(r"gs://[A-Za-z0-9][A-Za-z0-9._${}/-]*", re.IGNORECASE)
_GS_PLACEHOLDER = re.compile(
    r"gs://(?:YOUR_PRIVATE_BUCKET|YOUR_BUCKET|EXAMPLE_BUCKET)(?:/|$)",
    re.IGNORECASE,
)


def find_pii_markers(text: str) -> list[str]:
    """Heuristic markers for *public* trees — never encode real site strings here."""
    hits: list[str] = []
    if _STREET_LIKE.search(text):
        hits.append("street_like_address")
    for m in _GS_URI.finditer(text):
        uri = m.group(0)
        # Skip shell/template interpolations and documented placeholders.
        if "$" in uri or "{" in uri or _GS_PLACEHOLDER.search(uri):
            continue
        hits.append("private_gs_uri")
        break
    return hits


def scan_paths(paths: list[Path]) -> dict[str, list[str]]:
    """Scan files for PII markers. Missing/unreadable paths fail closed."""
    out: dict[str, list[str]] = {}
    for p in paths:
        if not p.is_file():
            out[str(p)] = ["missing_or_unreadable"]
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError as exc:
            out[str(p)] = [f"read_error:{exc.__class__.__name__}"]
            continue
        hits = find_pii_markers(text)
        if hits:
            out[str(p)] = hits
    return out
