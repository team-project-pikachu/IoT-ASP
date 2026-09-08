#!/usr/bin/env python3
"""Issue #16 verification: NS/seismo priors in autoroute path + negative control.

Writes artifacts under .vv/16/artifacts/. No GCP / Vercel required.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "services" / "autoroute-adk"
sys.path.insert(0, str(PKG))

from iot_asp_autoroute.priors import (  # noqa: E402
    CITATIONS,
    VIB_ALGO_WEIGHTS,
    filter_prior_keys,
    lf_drive_capable,
    preferred_algos,
    prior_text,
    seismo_bundle,
)
from iot_asp_autoroute.sudden_freq import author_sudden_freq_patch  # noqa: E402
from iot_asp_autoroute.tools import seismo_acoustic_priors  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"
ART = Path(__file__).resolve().parent / "artifacts"
ART.mkdir(parents=True, exist_ok=True)

results: list[dict] = []


def check(name: str, ok: bool, detail: str) -> None:
    results.append({"check": name, "pass": ok, "detail": detail})
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: {detail}")


def load(name: str) -> dict:
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def main() -> int:
    bundle = seismo_acoustic_priors()
    check(
        "REQ-16-01-tool-weights",
        "weights" in bundle and "physical" in bundle["weights"],
        f"keys={sorted(bundle.keys())}",
    )
    check(
        "REQ-16-02-citations",
        len(CITATIONS) >= 4 and all("id" in c and "url" in c for c in CITATIONS),
        f"n={len(CITATIONS)} ids={[c['id'] for c in CITATIONS]}",
    )
    check(
        "REQ-16-03-prior-coeffs",
        set(VIB_ALGO_WEIGHTS) >= {"physical", "acoustic", "infra_felt", "none"},
        f"classes={sorted(VIB_ALGO_WEIGHTS)}",
    )

    # Negative: nonsense prior keys ignored
    filtered = filter_prior_keys(["asdf_bogus_prior", "made_up_doi", "sudden_freq"])
    check(
        "REQ-16-04-neg-nonsense-keys",
        filtered == ["sudden_freq"] and prior_text(["zzz"]) == "",
        f"filtered={filtered}",
    )

    phys = load("synthetic_physical.json")
    ok, msg, patch_p = author_sudden_freq_patch(phys)
    (ART / "patch_physical.json").write_text(json.dumps(patch_p, indent=2), encoding="utf-8")
    check("REQ-16-05-physical-author", ok, msg)
    check(
        "REQ-16-06-physical-algo",
        patch_p.get("algo") in preferred_algos("physical", "table"),
        f"algo={patch_p.get('algo')} preferred={preferred_algos('physical', 'table')}",
    )
    check(
        "REQ-16-07-physical-band-us",
        patch_p.get("band") == "17-23k" and float(patch_p.get("fMin", 0)) >= 17000,
        f"band={patch_p.get('band')} fMin={patch_p.get('fMin')}",
    )
    check(
        "REQ-16-08-structure-prior",
        "structure_borne" in (patch_p.get("priors") or []),
        f"priors={patch_p.get('priors')}",
    )

    infra_ok = load("synthetic_infra_felt_capable.json")
    ok2, msg2, patch_i = author_sudden_freq_patch(infra_ok)
    (ART / "patch_infra_felt_capable.json").write_text(
        json.dumps(patch_i, indent=2), encoding="utf-8"
    )
    check("REQ-16-09-infra-capable-author", ok2, msg2)
    check(
        "REQ-16-10-lf-gated-when-capable",
        lf_drive_capable(infra_ok)
        and patch_i.get("band") == "10-20"
        and 10 <= float(patch_i.get("fMin", 0)) <= 20,
        f"band={patch_i.get('band')} f=[{patch_i.get('fMin')},{patch_i.get('fMax')}] "
        f"algo={patch_i.get('algo')} lf={patch_i.get('lfDriveCapable')}",
    )
    check(
        "REQ-16-11-infra-mod-weight",
        patch_i.get("algo") in ("infra_mod", "am_gate", "burst"),
        f"algo={patch_i.get('algo')} weights={patch_i.get('priorWeights')}",
    )
    check(
        "REQ-16-12-infra-prior-key",
        "infra_felt" in (patch_i.get("priors") or []),
        f"priors={patch_i.get('priors')}",
    )

    infra_na = load("synthetic_infra_felt_incapable.json")
    ok3, msg3, patch_n = author_sudden_freq_patch(infra_na)
    (ART / "patch_infra_felt_incapable.json").write_text(
        json.dumps(patch_n, indent=2), encoding="utf-8"
    )
    check("REQ-16-13-infra-incapable-author", ok3, msg3)
    check(
        "REQ-16-14-lf-blocked-when-incapable",
        not lf_drive_capable(infra_na) and patch_n.get("band") == "17-23k",
        f"band={patch_n.get('band')} lfCapable={lf_drive_capable(infra_na)}",
    )

    neg = load("negative_nonsense_priors.json")
    ok4, msg4, patch_neg = author_sudden_freq_patch(neg)
    (ART / "patch_negative_nonsense.json").write_text(
        json.dumps(patch_neg, indent=2), encoding="utf-8"
    )
    check("REQ-16-15-neg-author", ok4, msg4)
    check(
        "REQ-16-16-neg-fallback-vib-none",
        patch_neg.get("algo") in preferred_algos("none"),
        f"algo={patch_neg.get('algo')} (bogus vibClass → none weights)",
    )
    check(
        "REQ-16-17-neg-no-bogus-in-priors",
        all(k in seismo_bundle()["keys"] for k in (patch_neg.get("priors") or [])),
        f"priors={patch_neg.get('priors')}",
    )
    check(
        "REQ-16-18-literature-on-patch",
        bool(patch_p.get("literature")) and "arxiv:" in str(patch_p.get("literature")[0]),
        f"literature={patch_p.get('literature')}",
    )

    summary = {
        "issue": 16,
        "title": "NS / seismo-acoustic priors wire-up",
        "ranAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "revisionHint": "git rev-parse HEAD at evidence write time",
        "checks": results,
        "pass": all(r["pass"] for r in results),
        "failCount": sum(1 for r in results if not r["pass"]),
    }
    (ART / "verify_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"pass": summary["pass"], "failCount": summary["failCount"]}, indent=2))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
