#!/usr/bin/env python3
"""Analyze docs/ for structure, orphans, broken links, size, readability.

Stdlib only. Exit non-zero when a hard-fail category is hit.

Env knobs:
  DOCS_ANALYZER_FAIL_ON     comma list: broken_links (default), orphans, large,
                            duplicate_h1, readability, missing_tldr, all, none
  DOCS_ANALYZER_LINE_THRESHOLD   default 400
  DOCS_ANALYZER_PARA_WORDS       default 120 (flag paragraphs over this many words)
  DOCS_ANALYZER_ROOT             default: <repo>/docs
  DOCS_ANALYZER_INDEX            default: README.md (under docs root)
"""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = Path(os.environ.get("DOCS_ANALYZER_ROOT", REPO_ROOT / "docs")).resolve()
INDEX_NAME = os.environ.get("DOCS_ANALYZER_INDEX", "README.md")
LINE_THRESHOLD = int(os.environ.get("DOCS_ANALYZER_LINE_THRESHOLD", "400"))
PARA_WORDS = int(os.environ.get("DOCS_ANALYZER_PARA_WORDS", "120"))

# Canon docs that should carry a TL;DR for humans.
CANON_TLDR = frozenset(
    {
        "README.md",
        "PRD.md",
        "roadmap.md",
        "architecture-pwa.md",
        "UAT.md",
        "TESTING_PLAN.md",
        "api-contract.md",
        "DESIGN_CONSTRAINTS.md",
    }
)

# Paths under docs/ that may be unlinked from the index without orphan warning.
ORPHAN_ALLOW_PREFIXES = (
    "issues/",
    "specs/",  # specs have their own README; still prefer linking specs/README
)

MD_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
H1_RE = re.compile(r"^#\s+(.+)$", re.M)
TLDR_RE = re.compile(r"(?i)^\*\*TL;DR:?\*\*|^##\s*TL;DR\b|^>\s*\*\*TL;DR", re.M)


def fail_categories() -> set[str]:
    raw = os.environ.get("DOCS_ANALYZER_FAIL_ON", "broken_links").strip().lower()
    if raw in {"", "none"}:
        return set()
    if raw == "all":
        return {
            "broken_links",
            "orphans",
            "large",
            "duplicate_h1",
            "readability",
            "missing_tldr",
        }
    return {p.strip() for p in raw.split(",") if p.strip()}


def list_markdown() -> list[Path]:
    files = sorted(p for p in DOCS_ROOT.rglob("*.md") if p.is_file())
    return files


def rel_docs(path: Path) -> str:
    return path.relative_to(DOCS_ROOT).as_posix()


def extract_md_links(text: str) -> list[str]:
    out: list[str] = []
    for raw in MD_LINK_RE.findall(text):
        target = raw.strip().split()[0].strip("<>")
        if not target or target.startswith("#"):
            continue
        parsed = urlparse(target)
        if parsed.scheme in {"http", "https", "mailto", "data"}:
            continue
        if target.startswith("mailto:"):
            continue
        out.append(unquote(parsed.path or target.split("#")[0]))
    return out


def resolve_link(from_file: Path, link: str) -> Path | None:
    if not link or link.startswith("//"):
        return None
    # Absolute-from-repo rare; treat as relative to from_file parent
    base = from_file.parent
    candidate = (base / link).resolve()
    return candidate


def collect_index_targets(index_path: Path) -> set[str]:
    """Relative docs paths reachable from the index (one hop + self)."""
    text = index_path.read_text(encoding="utf-8", errors="replace")
    linked: set[str] = {rel_docs(index_path)}
    for link in extract_md_links(text):
        resolved = resolve_link(index_path, link)
        if resolved is None:
            continue
        try:
            if resolved.is_file() and DOCS_ROOT in resolved.parents or resolved.parent == DOCS_ROOT:
                if resolved.suffix.lower() == ".md" and str(resolved).startswith(str(DOCS_ROOT)):
                    linked.add(rel_docs(resolved))
        except ValueError:
            continue
        # Also allow directory README via trailing slash-ish links
        if resolved.is_dir():
            readme = resolved / "README.md"
            if readme.is_file():
                linked.add(rel_docs(readme))
    return linked


def paragraph_word_counts(text: str) -> list[tuple[int, int]]:
    """Return (approx line, word_count) for long prose paragraphs."""
    hits: list[tuple[int, int]] = []
    # Split on blank lines; skip fenced code
    in_fence = False
    buf: list[str] = []
    start_line = 1
    line_no = 0
    for line in text.splitlines():
        line_no += 1
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line.strip():
            if buf:
                para = " ".join(buf)
                # skip tables / headings / pure lists
                if not para.startswith("#") and not para.startswith("|") and not para.startswith("- "):
                    words = len(re.findall(r"\b\w+\b", para))
                    if words >= PARA_WORDS:
                        hits.append((start_line, words))
            buf = []
            start_line = line_no + 1
        else:
            if not buf:
                start_line = line_no
            # skip list continuations for wall detection when line starts with list marker
            if line.lstrip().startswith(("-", "*", ">")) and not buf:
                continue
            buf.append(line.strip())
    if buf:
        para = " ".join(buf)
        if not para.startswith("#") and not para.startswith("|"):
            words = len(re.findall(r"\b\w+\b", para))
            if words >= PARA_WORDS:
                hits.append((start_line, words))
    return hits


def main() -> int:
    if not DOCS_ROOT.is_dir():
        print(f"ERROR: docs root missing: {DOCS_ROOT}", file=sys.stderr)
        return 2

    files = list_markdown()
    index_path = DOCS_ROOT / INDEX_NAME
    if not index_path.is_file():
        print(f"ERROR: index missing: {index_path}", file=sys.stderr)
        return 2

    broken: list[str] = []
    large: list[str] = []
    h1_map: dict[str, list[str]] = defaultdict(list)
    missing_tldr: list[str] = []
    long_paras: list[str] = []
    index_links = collect_index_targets(index_path)
    orphans: list[str] = []

    print(f"## Docs analyzer")
    print(f"- root: {DOCS_ROOT}")
    print(f"- markdown files: {len(files)}")
    print(f"- index: {INDEX_NAME} ({len(index_links)} linked targets)")
    print(f"- fail_on: {sorted(fail_categories()) or ['(warnings only)']}")
    print()

    print("### Inventory")
    for path in files:
        rel = rel_docs(path)
        lines = path.read_text(encoding="utf-8", errors="replace").count("\n") + 1
        print(f"- {rel} ({lines} lines)")
        if lines >= LINE_THRESHOLD:
            large.append(f"{rel}: {lines} lines (>= {LINE_THRESHOLD})")

    print()
    print("### Checks")

    for path in files:
        rel = rel_docs(path)
        text = path.read_text(encoding="utf-8", errors="replace")

        for m in H1_RE.finditer(text):
            title = m.group(1).strip().lower()
            h1_map[title].append(rel)

        if rel in CANON_TLDR:
            # README is the index; require either TL;DR or "Start here"
            if rel == INDEX_NAME:
                if "Start here" not in text and not TLDR_RE.search(text):
                    missing_tldr.append(rel)
            elif not TLDR_RE.search(text):
                missing_tldr.append(rel)

        for start, words in paragraph_word_counts(text):
            long_paras.append(f"{rel}:{start}: ~{words} words")

        for link in extract_md_links(text):
            # skip pure anchors already filtered
            if link.startswith("#"):
                continue
            resolved = resolve_link(path, link)
            if resolved is None:
                continue
            # Allow links outside docs/ that exist in repo
            if not resolved.exists():
                # common: link to sibling without .md still missing
                broken.append(f"{rel} → {link} (missing {resolved})")

        # orphan: not linked from index, not allowlisted prefix, not the index
        if rel != INDEX_NAME and rel not in index_links:
            if not any(rel.startswith(p) for p in ORPHAN_ALLOW_PREFIXES):
                orphans.append(rel)

    dup_h1 = {t: paths for t, paths in h1_map.items() if len(paths) > 1}

    def section(title: str, items: list[str], empty: str = "none") -> None:
        print(f"\n#### {title} ({len(items)})")
        if not items:
            print(f"- {empty}")
            return
        for item in items[:80]:
            print(f"- {item}")
        if len(items) > 80:
            print(f"- … +{len(items) - 80} more")

    section("Broken relative links", broken)
    section("Orphans (not linked from docs/README.md)", orphans)
    section(f"Large files (>={LINE_THRESHOLD} lines)", large)
    dup_items = [f"{title!r}: {', '.join(paths)}" for title, paths in sorted(dup_h1.items())]
    section("Duplicate H1 titles", dup_items)
    section("Missing TL;DR on canonical docs", missing_tldr)
    section(f"Long paragraphs (>={PARA_WORDS} words)", long_paras)

    fails = fail_categories()
    hard: list[str] = []
    if "broken_links" in fails and broken:
        hard.append(f"broken_links={len(broken)}")
    if "orphans" in fails and orphans:
        hard.append(f"orphans={len(orphans)}")
    if "large" in fails and large:
        hard.append(f"large={len(large)}")
    if "duplicate_h1" in fails and dup_items:
        hard.append(f"duplicate_h1={len(dup_items)}")
    if "missing_tldr" in fails and missing_tldr:
        hard.append(f"missing_tldr={len(missing_tldr)}")
    if "readability" in fails and (long_paras or missing_tldr):
        hard.append(f"readability=paras:{len(long_paras)}+tldr:{len(missing_tldr)}")

    print()
    print("### Summary")
    print(
        f"broken={len(broken)} orphans={len(orphans)} large={len(large)} "
        f"dup_h1={len(dup_items)} missing_tldr={len(missing_tldr)} long_paras={len(long_paras)}"
    )
    if hard:
        print(f"FAIL: {', '.join(hard)}")
        return 1
    print("OK (no hard-fail categories triggered)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
