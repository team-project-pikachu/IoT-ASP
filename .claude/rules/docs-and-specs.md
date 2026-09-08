---
paths:
  - "docs/**"
  - "SPEC.md"
  - "README.md"
  - "reference/**"
  - ".vv/**"
---

# Docs, specs, evidence

- One spec per Project 5 issue in `docs/specs/<issue>-<slug>.md` with sections: Status · Goal · Prior art (what already exists here, on the owner's Mac clone, in org repos, in awesome-lists / OSS, and why we reuse or build) · Shipped on `main` (cite `file:line`) · Remaining scope · Wire fields · Clamps / safety · Acceptance tests · CI gate · Risks / HW limits · Sources.
- `docs/api-contract.md` is canonical for telemetry/patch fields. Other docs link to it; never fork field tables.
- `SPEC.md` = Soundcore 2 manufacturer limits + fleet topology + index of feature specs. Product-spec rules converted from `.mdc` land in `SPEC.md` managed blocks.
- Every factual claim about a library, API, or vendor carries a source (Context7 library id, docs URL, DOI/arXiv/PMID from `reference/LITERATURE.md`). No fabricated citations.
- Public docs stay generic: no street addresses, neighbor identifiers, recording URIs, seat emails. Site protocol lives in gitignored `study/`.
- `.vv/<area>/*.md` evidence files record: config item, date (UTC), procedure (commands), observed results with exit codes, pass/fail table. No secret values, ever.
- Several docs referenced from `docs/awesome-iot-asp.md` exist only on the owner's Mac (not on `origin/main`): `materials-engineering.md`, `mvp-tooling.md`, `well-architected-ai.md`, `similar-projects.md`, `ux-*.md`, `native-xcode.md`, `timestore.md`, `dependencies.md`. Do not create placeholder copies; note the gap in `docs/specs/README.md`.
