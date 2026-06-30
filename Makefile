.PHONY: check demo clean
PYTHON ?= python3
check:
	$(PYTHON) -m py_compile scripts/*.py tests/*.py
	$(PYTHON) scripts/vaultctx.py validate
	$(PYTHON) -m pytest -q
	$(PYTHON) scripts/vaultctx.py scan-daily
	$(PYTHON) scripts/vaultctx.py extract
	$(PYTHON) scripts/vaultctx.py render-views
	$(PYTHON) scripts/vaultctx.py build-sqlite
	$(PYTHON) scripts/vaultctx.py bundle --goal "plan the week" > /tmp/minimal-ai-vault-starter-bundle.json
	$(PYTHON) scripts/vaultctx.py validate

demo:
	$(PYTHON) scripts/vaultctx.py scan-daily
	$(PYTHON) scripts/vaultctx.py extract
	$(PYTHON) scripts/vaultctx.py render-views
	$(PYTHON) scripts/vaultctx.py bundle --goal "plan the week"

clean:
	rm -f dist/*.sqlite
	rm -rf dist/bundles dist/human_owned_hashes.json
