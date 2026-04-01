PYTHON ?= python3
URL ?= https://example.com
BRAND ?=

.PHONY: help setup check audit clean-generated clean-generated-with-caches brand-example brand-example-interactive

help:
	@echo "Available commands:"
	@echo "  make setup              Install local dependencies on macOS/Linux"
	@echo "  make check              Verify the local setup"
	@echo "  make audit URL=<site> [BRAND=path/to/brand.yml]   Run a full audit for the given site"
	@echo "  make clean-generated    Remove generated run artifacts"
	@echo "  make clean-generated-with-caches Remove generated artifacts and Python caches"
	@echo "  make brand-example      Create branding/my-brand from the example template"
	@echo "  make brand-example-interactive Create branding/my-brand and ask for company details"

setup:
	./setup_local.sh

check:
	$(PYTHON) run_audit.py --help
	go version
	$(PYTHON) --version
	node --version
	pandoc --version

audit:
	$(PYTHON) run_audit.py "$(URL)" $(if $(BRAND),--brand "$(BRAND)")

clean-generated:
	$(PYTHON) cleanup_generated_artifacts.py --yes

clean-generated-with-caches:
	$(PYTHON) cleanup_generated_artifacts.py --include-caches --yes

brand-example:
	$(PYTHON) create_branding_bundle.py

brand-example-interactive:
	$(PYTHON) create_branding_bundle.py --interactive
