"""Resolve private study roots without publishing their contents."""

from __future__ import annotations

import os
from pathlib import Path

# Env wins; then conventional gitignored ./study next to the IoT-ASP checkout.
_ENV = "IOT_ASP_STUDY_ROOT"


def resolve_study_root(start: Path | None = None) -> Path | None:
    """Return a directory that exists for private study material, or None.

    Order:
    1. ``IOT_ASP_STUDY_ROOT`` (clone of IoT-ASP-study or its ``study/`` subdir)
    2. ``<repo>/study`` when present (gitignored local mirror)
    """
    env = os.environ.get(_ENV, "").strip()
    if env:
        p = Path(env).expanduser().resolve()
        if p.is_dir():
            # Accept either repo root (has study/) or the study/ folder itself.
            if (p / "study").is_dir():
                return p / "study"
            return p
        return None

    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        study = candidate / "study"
        if study.is_dir():
            return study
        # Stop at filesystem root / unlikely repo boundary
        if (candidate / ".git").exists() and candidate != here:
            # checked this repo's study already via parents walk
            pass
        if candidate.parent == candidate:
            break
    return None
