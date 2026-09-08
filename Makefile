# IoT-ASP — deterministic local entry points (mirror .github/workflows/ci.yml)
.PHONY: help deps gates dryrun test mdc mdc-check native-check sensorkit-stub-build all e2e protect-main

PY ?= python3

help:
	@echo "make deps       # pip install -r requirements-dev.txt"
	@echo "make gates      # scripts/ci_static_gates.sh (Hold/Manual, no keys, schemaVersion, clamps)"
	@echo "make dryrun     # scripts/autoroute_dev.sh (offline suddenFreq → clamped patch)"
	@echo "make test       # pytest tests/"
	@echo "make mdc        # convert .cursor/rules/*.mdc → CLAUDE.md blocks + .claude/rules + .claude/skills"
	@echo "make mdc-check  # fail if converted outputs are stale (CI gate)"
	@echo "make native-check  # CLT swift smoke + SPM resolve (#41; no Xcode.app claim)"
	@echo "make sensorkit-stub-build  # M9 SensorKit stub SPM (#110; no entitlement)"
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

native-check:
	bash scripts/native_compile_check.sh

sensorkit-stub-build:
	bash scripts/sensorkit_stub_build.sh

all: gates dryrun test mdc-check

e2e:
	@test -f tests/e2e/run.sh || { echo "tests/e2e/run.sh not found — the Playwright smoke lives in tests/e2e/ (see docs/specs/01-m0-public-blaster.md)"; exit 1; }
	bash tests/e2e/run.sh

protect-main:
	@test -f scripts/gh_protect_main.sh || { echo "scripts/gh_protect_main.sh not found — see docs/branch-protection.md"; exit 1; }
	bash scripts/gh_protect_main.sh
