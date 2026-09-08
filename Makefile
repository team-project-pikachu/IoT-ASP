# IoT-ASP — deterministic local entry points (mirror .github/workflows/ci.yml)
.PHONY: help deps gates dryrun test mdc mdc-check home-ios-build home-gcloud-dry all e2e protect-main

PY ?= python3

help:
	@echo "make deps       # pip install -r requirements-dev.txt"
	@echo "make gates      # scripts/ci_static_gates.sh (Hold/Manual, no keys, schemaVersion, clamps)"
	@echo "make dryrun     # scripts/autoroute_dev.sh (offline suddenFreq → clamped patch)"
	@echo "make test       # pytest tests/"
	@echo "make mdc        # convert .cursor/rules/*.mdc → CLAUDE.md blocks + .claude/rules + .claude/skills"
	@echo "make mdc-check  # fail if converted outputs are stale (CI gate)"
	@echo "make home-ios-build  # M8 native/IoTASPHome stub swift build (no GoogleHomeSDK)"
	@echo "make home-gcloud-dry # M8 gcloud Home/Vertex bootstrap dry-run"
	@echo "make all        # gates + dryrun + test + mdc-check"
	@echo "make e2e        # Playwright smoke against public/ (see tests/e2e/)"
	@echo "make protect-main  # apply .github/rulesets/main-protection.json via gh api (run on a machine with gh)"

deps:
	$(PY) -m pip install -r requirements-dev.txt

gates:
	bash scripts/ci_static_gates.sh

dryrun:
	bash scripts/autoroute_dev.sh

test:
	$(PY) -m pytest tests -q

mdc:
	$(PY) scripts/mdc_convert.py

mdc-check:
	$(PY) scripts/mdc_convert.py --check

home-ios-build:
	bash scripts/home_ios_build.sh

home-gcloud-dry:
	bash scripts/home_apis_gcloud_bootstrap.sh

all: gates dryrun test mdc-check

e2e:
	@test -f tests/e2e/run.sh || { echo "tests/e2e/run.sh not found — the Playwright smoke lives in tests/e2e/ (see docs/specs/01-m0-public-blaster.md)"; exit 1; }
	bash tests/e2e/run.sh

protect-main:
	@test -f scripts/gh_protect_main.sh || { echo "scripts/gh_protect_main.sh not found — see docs/branch-protection.md"; exit 1; }
	bash scripts/gh_protect_main.sh
