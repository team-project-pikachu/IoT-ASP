"""Tests for scripts/mdc_convert.py — deterministic Cursor .mdc → Claude Code converter."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mdc_convert.py"


def _load():
    spec = importlib.util.spec_from_file_location("mdc_convert", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["mdc_convert"] = mod  # dataclasses need the module registered to resolve annotations
    spec.loader.exec_module(mod)
    return mod


mdc = _load()


# ── fixture repo ─────────────────────────────────────────────────────────────

ALWAYS = """---
description: Always-on project conventions
globs:
alwaysApply: true
---
# Conventions

- Use tabs? No, spaces.
- Cite sources.
"""

AUTO_CSV = """---
description: Frontend rules
globs: public/**/*.html, public/*.json
alwaysApply: false
---
- Keep Hold / Manual.
"""

AUTO_LIST = """---
description:
globs:
  - "services/**/*.py"
  - tests/**/*.py
alwaysApply: false
---
Backend rules body.
"""

AGENT = """---
description: RPC service conventions: patterns for the backend
alwaysApply: false
---
- Validate inputs at the boundary.
"""

MANUAL = """---
description:
globs:
alwaysApply: false
---
Manual only body.
"""

NESTED_ALWAYS = """---
alwaysApply: true
---
Nested package rules.
"""

SPEC_RULE = """---
description: Product spec for prior art
alwaysApply: false
---
## Requirements

- R1 must hold.
"""

NO_FM = "No frontmatter at all.\n"

UNQUOTED_STAR = """---
description: star globs
globs: *.ts, **/*.tsx
alwaysApply: false
---
Star body.
"""


def make_repo(tmp_path: Path, *, with_config: bool = True) -> Path:
    root = tmp_path / "repo"
    rules = root / ".cursor" / "rules"
    rules.mkdir(parents=True)
    (rules / "always-rule.mdc").write_text(ALWAYS, encoding="utf-8")
    (rules / "auto_csv.mdc").write_text(AUTO_CSV, encoding="utf-8")
    (rules / "auto-list.mdc").write_text(AUTO_LIST, encoding="utf-8")
    (rules / "agent-rule.mdc").write_text(AGENT, encoding="utf-8")
    (rules / "manual-rule.mdc").write_text(MANUAL, encoding="utf-8")
    (rules / "asp-prior-art.mdc").write_text(SPEC_RULE, encoding="utf-8")
    (rules / "nofm.mdc").write_text(NO_FM, encoding="utf-8")
    (rules / "star.mdc").write_text(UNQUOTED_STAR, encoding="utf-8")
    nested = root / "pkg" / ".cursor" / "rules"
    nested.mkdir(parents=True)
    (nested / "nested.mdc").write_text(NESTED_ALWAYS, encoding="utf-8")
    (root / ".cursorrules").write_text("Legacy top-level rules.\n", encoding="utf-8")
    (root / "CLAUDE.md").write_text(
        "# Handwritten memory\n\nKeep me.\n\n<!-- mdc:managed-section -->\n\n## Trailing handwritten\n\nAlso keep me.\n",
        encoding="utf-8",
    )
    (root / "SPEC.md").write_text("# Spec\n\nManufacturer table.\n", encoding="utf-8")
    hand = root / ".claude" / "rules"
    hand.mkdir(parents=True)
    (hand / "handwritten.md").write_text("---\npaths:\n  - \"x/**\"\n---\nHand written, never touched.\n", encoding="utf-8")
    if with_config:
        (root / ".mdc-convert.json").write_text(json.dumps({"spec": ["asp-prior-art"]}), encoding="utf-8")
    return root


def snapshot(root: Path) -> dict[str, str]:
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[p.relative_to(root).as_posix()] = p.read_text(encoding="utf-8")
    return out


# ── parser ───────────────────────────────────────────────────────────────────


def test_frontmatter_csv_globs_and_bool():
    meta, body, had = mdc.parse_frontmatter(AUTO_CSV)
    assert had
    assert mdc._split_globs(meta["globs"]) == ["public/**/*.html", "public/*.json"]
    assert mdc._to_bool(meta["alwaysApply"]) is False
    assert body.strip() == "- Keep Hold / Manual."


def test_frontmatter_list_globs_and_empty_description():
    meta, _, _ = mdc.parse_frontmatter(AUTO_LIST)
    assert meta["description"] is None
    assert mdc._split_globs(meta["globs"]) == ["services/**/*.py", "tests/**/*.py"]


def test_frontmatter_unquoted_star_globs_not_yaml_alias():
    meta, _, _ = mdc.parse_frontmatter(UNQUOTED_STAR)
    assert mdc._split_globs(meta["globs"]) == ["*.ts", "**/*.tsx"]


def test_frontmatter_inline_list_and_true_variants():
    meta, _, _ = mdc.parse_frontmatter('---\nglobs: ["a/**", \'b/*.py\']\nalwaysApply: True\n---\nx\n')
    assert mdc._split_globs(meta["globs"]) == ["a/**", "b/*.py"]
    assert mdc._to_bool(meta["alwaysApply"]) is True


def test_no_frontmatter_is_manual():
    meta, body, had = mdc.parse_frontmatter(NO_FM)
    assert not had and meta == {} and body == NO_FM
    assert mdc.classify(meta, had) == "manual"


@pytest.mark.parametrize(
    "meta,expected",
    [
        ({"alwaysApply": "true", "globs": "a/**", "description": "d"}, "always"),
        ({"alwaysApply": "false", "globs": "a/**", "description": "d"}, "auto"),
        ({"alwaysApply": "false", "globs": None, "description": "d"}, "agent"),
        ({"alwaysApply": "false", "globs": None, "description": None}, "manual"),
        ({}, "manual"),
    ],
)
def test_classify_table(meta, expected):
    assert mdc.classify(meta, True) == expected


# ── end-to-end ───────────────────────────────────────────────────────────────


def test_convert_fixture_repo(tmp_path):
    root = make_repo(tmp_path)
    assert mdc.main(["--root", str(root)]) == 0
    files = snapshot(root)

    # Always → CLAUDE.md managed block, handwritten text preserved on both sides of the anchor
    claude = files["CLAUDE.md"]
    assert claude.startswith("# Handwritten memory\n\nKeep me.\n")
    assert "## Trailing handwritten\n\nAlso keep me." in claude
    assert "<!-- mdc:begin always-rule source=.cursor/rules/always-rule.mdc sha256=" in claude
    assert "<!-- mdc:end always-rule -->" in claude
    assert "<!-- mdc:begin cursorrules source=.cursorrules" in claude
    assert claude.index("<!-- mdc:managed-section -->") < claude.index("mdc:begin always-rule") < claude.index("## Trailing handwritten")

    # Auto attached → .claude/rules with paths frontmatter
    rule_csv = files[".claude/rules/auto-csv.md"]
    assert rule_csv.startswith('---\npaths:\n  - "public/**/*.html"\n  - "public/*.json"\n---\n')
    assert mdc.GEN_MARK in rule_csv
    assert "# Frontend rules" in rule_csv and "- Keep Hold / Manual." in rule_csv
    rule_list = files[".claude/rules/auto-list.md"]
    assert '  - "services/**/*.py"\n  - "tests/**/*.py"' in rule_list
    assert '  - "*.ts"\n  - "**/*.tsx"' in files[".claude/rules/star.md"]

    # Nested alwaysApply → scoped path rule
    nested = files[".claude/rules/nested.md"]
    assert '  - "pkg/**"' in nested

    # Agent requested + manual → skills
    agent = files[".claude/skills/agent-rule/SKILL.md"]
    assert agent.startswith("---\nname: agent-rule\ndescription: \"RPC service conventions: patterns for the backend\"\n---\n")
    manual = files[".claude/skills/manual-rule/SKILL.md"]
    assert "description: Manual Cursor rule manual-rule; invoke with /manual-rule" in manual
    assert "Manual only body." in manual
    assert "nofm/SKILL.md" in "\n".join(files) and "No frontmatter at all." in files[".claude/skills/nofm/SKILL.md"]

    # Config-routed spec → SPEC.md managed block appended, existing content kept
    spec = files["SPEC.md"]
    assert spec.startswith("# Spec\n\nManufacturer table.\n")
    assert "## Converted rule specs" in spec and "<!-- mdc:begin asp-prior-art" in spec and "- R1 must hold." in spec

    # Handwritten rule file untouched
    assert files[".claude/rules/handwritten.md"].endswith("Hand written, never touched.\n")

    # Manifest is deterministic + complete
    manifest = json.loads(files[".claude/mdc-manifest.json"])
    by_slug = {r["slug"]: r for r in manifest["rules"]}
    assert by_slug["always-rule"]["target"] == "claude"
    assert by_slug["auto-csv"]["target"] == "rule"
    assert by_slug["agent-rule"]["target"] == "skill"
    assert by_slug["asp-prior-art"]["target"] == "spec"
    assert by_slug["nested"]["scope"] == "pkg/" and by_slug["nested"]["globs"] == ["pkg/**"]
    assert list(by_slug) == sorted(by_slug, key=lambda s: by_slug[s]["source"])


def test_idempotent_and_check_gate(tmp_path, capsys):
    root = make_repo(tmp_path)
    assert mdc.main(["--root", str(root)]) == 0
    first = snapshot(root)
    assert mdc.main(["--root", str(root)]) == 0
    assert snapshot(root) == first, "second run must be a no-op"
    assert mdc.main(["--root", str(root), "--check"]) == 0
    # edit a source → check fails, convert repairs, check passes
    (root / ".cursor/rules/always-rule.mdc").write_text(ALWAYS + "- New bullet.\n", encoding="utf-8")
    assert mdc.main(["--root", str(root), "--check"]) == 1
    assert "STALE" in capsys.readouterr().err
    assert mdc.main(["--root", str(root)]) == 0
    assert "- New bullet." in (root / "CLAUDE.md").read_text(encoding="utf-8")
    assert mdc.main(["--root", str(root), "--check"]) == 0


def test_prune_stale_generated_outputs(tmp_path):
    root = make_repo(tmp_path)
    mdc.main(["--root", str(root)])
    assert (root / ".claude/rules/auto-csv.md").is_file()
    assert (root / ".claude/skills/agent-rule/SKILL.md").is_file()
    (root / ".cursor/rules/auto_csv.mdc").unlink()
    (root / ".cursor/rules/agent-rule.mdc").unlink()
    (root / ".cursor/rules/always-rule.mdc").unlink()
    assert mdc.main(["--root", str(root)]) == 0
    assert not (root / ".claude/rules/auto-csv.md").exists()
    assert not (root / ".claude/skills/agent-rule").exists()
    claude = (root / "CLAUDE.md").read_text(encoding="utf-8")
    assert "mdc:begin always-rule" not in claude and "Keep me." in claude and "Also keep me." in claude
    assert (root / ".claude/rules/handwritten.md").is_file()


def test_no_sources_is_noop_and_check_passes(tmp_path, capsys):
    root = tmp_path / "empty"
    root.mkdir()
    (root / "CLAUDE.md").write_text("# Memory\n\n<!-- mdc:managed-section -->\n", encoding="utf-8")
    assert mdc.main(["--root", str(root), "--check"]) == 0
    out = capsys.readouterr().out
    assert "no .mdc sources found" in out
    assert mdc.main(["--root", str(root)]) == 0
    assert (root / "CLAUDE.md").read_text(encoding="utf-8") == "# Memory\n\n<!-- mdc:managed-section -->\n"
    assert not (root / ".claude").exists()


def test_claude_md_created_when_missing_and_always_rules_exist(tmp_path):
    root = tmp_path / "fresh"
    (root / ".cursor/rules").mkdir(parents=True)
    (root / ".cursor/rules/a.mdc").write_text(ALWAYS, encoding="utf-8")
    assert mdc.main(["--root", str(root)]) == 0
    text = (root / "CLAUDE.md").read_text(encoding="utf-8")
    assert text.startswith("# Project memory\n\n<!-- mdc:managed-section -->\n")
    assert "mdc:begin a " in text


def test_unknown_config_key_rejected(tmp_path):
    root = make_repo(tmp_path, with_config=False)
    (root / ".mdc-convert.json").write_text(json.dumps({"bogus": 1}), encoding="utf-8")
    with pytest.raises(SystemExit):
        mdc.main(["--root", str(root)])


def test_slug_collision_is_deterministic(tmp_path):
    root = tmp_path / "coll"
    (root / ".cursor/rules").mkdir(parents=True)
    (root / ".cursor/rules/My Rule.mdc").write_text(AGENT, encoding="utf-8")
    (root / ".cursor/rules/my-rule.mdc").write_text(AGENT, encoding="utf-8")
    assert mdc.main(["--root", str(root)]) == 0
    skills = sorted(p.name for p in (root / ".claude/skills").iterdir())
    assert skills == ["my-rule", "my-rule-2"]


def test_external_source_dir_via_src_flag(tmp_path):
    """Shared rules one level up (e.g. /Users/machine/apps/.cursor/rules) convert without scoping."""
    apps = tmp_path / "apps"
    shared = apps / ".cursor" / "rules"
    shared.mkdir(parents=True)
    (shared / "shared-always.mdc").write_text(ALWAYS, encoding="utf-8")
    (shared / "shared-auto.mdc").write_text(AUTO_CSV, encoding="utf-8")
    root = apps / "IoT-ASP"
    root.mkdir()
    (root / "CLAUDE.md").write_text("# Memory\n\n<!-- mdc:managed-section -->\n", encoding="utf-8")
    assert mdc.main(["--root", str(root), "--src", "../.cursor/rules"]) == 0
    claude = (root / "CLAUDE.md").read_text(encoding="utf-8")
    assert "mdc:begin shared-always source=../.cursor/rules/shared-always.mdc" in claude
    rule = (root / ".claude/rules/shared-auto.md").read_text(encoding="utf-8")
    assert '  - "public/**/*.html"' in rule  # not prefixed: external sources are never scoped
    manifest = json.loads((root / ".claude/mdc-manifest.json").read_text(encoding="utf-8"))
    assert {r["slug"] for r in manifest["rules"]} == {"shared-always", "shared-auto"}
    assert mdc.main(["--root", str(root), "--src", "../.cursor/rules", "--check"]) == 0


def test_refuse_overwrite_handwritten_without_gen_mark(tmp_path, capsys):
    """Matching .mdc must not clobber a hand-written .claude/rules file lacking GEN_MARK.

    Regression for the PR #29 review finding: adding
    ``.cursor/rules/autoroute-backend.mdc`` used to overwrite the hand-written
    ``.claude/rules/autoroute-backend.md`` (body became ``# OVERWRITTEN``).
    """
    root = tmp_path / "collision"
    rules_out = root / ".claude" / "rules"
    rules_out.mkdir(parents=True)
    hand = rules_out / "autoroute-backend.md"
    hand_body = "---\npaths:\n  - \"services/**\"\n---\n# Hand written — keep me\n"
    hand.write_text(hand_body, encoding="utf-8")
    (root / ".cursor" / "rules").mkdir(parents=True)
    (root / ".cursor" / "rules" / "autoroute-backend.mdc").write_text(
        "---\nglobs: services/**\nalwaysApply: false\n---\n# OVERWRITTEN\n",
        encoding="utf-8",
    )

    assert mdc.main(["--root", str(root)]) == 1
    err = capsys.readouterr().err
    assert "CONFLICT" in err and "GEN_MARK" in err
    assert hand.read_text(encoding="utf-8") == hand_body
    assert "# OVERWRITTEN" not in hand.read_text(encoding="utf-8")
    assert mdc.GEN_MARK not in hand.read_text(encoding="utf-8")

    # --check also refuses (does not report a silent STALE that invites clobber)
    assert mdc.main(["--root", str(root), "--check"]) == 1
    assert "CONFLICT" in capsys.readouterr().err

    # --dry-run reports the conflict but does not write
    assert mdc.main(["--root", str(root), "--dry-run"]) == 0
    assert hand.read_text(encoding="utf-8") == hand_body

    # --force opts in to the overwrite
    assert mdc.main(["--root", str(root), "--force"]) == 0
    after = hand.read_text(encoding="utf-8")
    assert mdc.GEN_MARK in after
    assert "# OVERWRITTEN" in after
    assert "Hand written — keep me" not in after


def test_generated_rule_still_updates_without_force(tmp_path):
    """Files that already carry GEN_MARK remain managed and update without --force."""
    root = make_repo(tmp_path)
    assert mdc.main(["--root", str(root)]) == 0
    target = root / ".claude" / "rules" / "auto-csv.md"
    assert mdc.GEN_MARK in target.read_text(encoding="utf-8")
    (root / ".cursor" / "rules" / "auto_csv.mdc").write_text(
        AUTO_CSV + "- Extra bullet.\n", encoding="utf-8"
    )
    assert mdc.main(["--root", str(root)]) == 0
    assert "- Extra bullet." in target.read_text(encoding="utf-8")


<<<<<<< HEAD
def test_long_frontmatter_gen_mark_not_misclassified(tmp_path):
    """GEN_MARK after a long paths frontmatter must still count as managed (no --force)."""
    root = tmp_path / "long-fm"
    (root / ".cursor" / "rules").mkdir(parents=True)
    # Many globs → rendered YAML paths: block pushes GEN_MARK well past 800 chars.
    globs = ", ".join(f"services/path{i:04d}/**/*.py" for i in range(80))
    (root / ".cursor" / "rules" / "long_globs.mdc").write_text(
        f"---\ndescription: Long globs regression\nglobs: {globs}\nalwaysApply: false\n---\n# Body\n",
        encoding="utf-8",
    )
    assert mdc.main(["--root", str(root)]) == 0
    target = root / ".claude" / "rules" / "long-globs.md"
    text = target.read_text(encoding="utf-8")
    assert mdc.GEN_MARK in text
    # Provenance comment must appear after a large frontmatter (regression vs [:800] scan).
    mark_at = text.index(mdc.GEN_MARK)
    assert mark_at > 800, mark_at
    # Second convert without --force must refresh (not refuse as hand-written).
    (root / ".cursor" / "rules" / "long_globs.mdc").write_text(
        f"---\ndescription: Long globs regression\nglobs: {globs}\nalwaysApply: false\n---\n# Body\n- refreshed\n",
        encoding="utf-8",
    )
    assert mdc.main(["--root", str(root)]) == 0
    assert "- refreshed" in target.read_text(encoding="utf-8")
    assert mdc.main(["--root", str(root), "--check"]) == 0


=======
>>>>>>> 80f65c0 (Refuse mdc_convert overwrite of hand-written Claude rules.)
def test_repo_itself_is_up_to_date():
    """The live repo must pass the CI gate (no .mdc committed here; outputs consistent)."""
    assert mdc.main(["--root", str(ROOT), "--check"]) == 0
