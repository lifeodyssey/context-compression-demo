.PHONY: reproduce test data
reproduce:
	bash scripts/run_all.sh

# Intentionally exits 1: the demo preserves one regression for the agent to fix.
test:
	pytest -v

data:
	python3 data/generate.py
