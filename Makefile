.PHONY: test lint validate health backup restore-test acceptance hps-plan

test:
	python3 -m pytest -q tests

lint:
	bash scripts/ci/format-lint.sh

validate:
	python3 scripts/ci/validate-config.py
	python3 scripts/ci/repository-policy.py
	python3 scripts/ci/fault-ledger-validate.py
	python3 scripts/ci/claim-evidence-validate.py
	python3 scripts/ci/docs-drift.py

health:
	bash scripts/healthcheck.sh

backup:
	bash scripts/backup.sh

restore-test:
	bash scripts/restore-test.sh

acceptance:
	bash scripts/acceptance.sh

hps-plan:
	HPS_ALLOW_NON_CLEANROOM=1 bash hps/bin/hps plan
