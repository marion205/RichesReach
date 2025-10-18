# Backend dependency management with pip-tools
# Usage:
#   make lock          # Generate/update constraints.lock from .in files
#   make sync          # Install exact deps from constraints.lock (dev/CI-friendly)
#   make check-lock    # Fail if constraints.lock is out-of-date (build guard)
#   make upgrade       # Lock + upgrade all deps (use sparingly)

.PHONY: lock sync check-lock upgrade clean

# Paths (tweak if needed)
REQUIREMENTS_IN := requirements.in
CONSTRAINTS_IN := constraints.in
LOCK_FILE := constraints.lock

# Detect if constraints.in exists
ifdef HAS_CONSTRAINTS
  INPUT_FILES := $(REQUIREMENTS_IN) $(CONSTRAINTS_IN)
else
  INPUT_FILES := $(REQUIREMENTS_IN)
  HAS_CONSTRAINTS :=
endif

lock:
	@echo "🔒 Compiling lockfile..."
	@if [ -f $(CONSTRAINTS_IN) ]; then \
		pip-compile --generate-hashes --resolver=backtracking --upgrade --output-file $(LOCK_FILE) $(INPUT_FILES); \
	else \
		pip-compile --generate-hashes --resolver=backtracking --upgrade --output-file $(LOCK_FILE) $(REQUIREMENTS_IN); \
	fi
	@echo "✅ $(LOCK_FILE) updated!"

sync:
	@echo "📦 Syncing from $(LOCK_FILE)..."
	pip install --no-deps --require-hashes -r $(LOCK_FILE)
	pip check
	@echo "✅ Deps synced & verified!"

check-lock:
	@echo "🛡️ Checking if $(LOCK_FILE) is up-to-date..."
	@if [ -f $(LOCK_FILE) ]; then \
		if ! pip-compile --generate-hashes --resolver=backtracking --dry-run --output-file $(LOCK_FILE) $(INPUT_FILES) 2>/dev/null; then \
			echo "❌ $(LOCK_FILE) is out-of-date! Run 'make lock' to update."; \
			exit 1; \
		fi; \
	else \
		echo "❌ No $(LOCK_FILE) found! Run 'make lock' first."; \
		exit 1; \
	fi
	@echo "✅ Lockfile is current."

upgrade:
	@echo "🚀 Upgrading all deps in lockfile..."
	@if [ -f $(CONSTRAINTS_IN) ]; then \
		pip-compile --generate-hashes --resolver=backtracking --upgrade-package all --output-file $(LOCK_FILE) $(INPUT_FILES); \
	else \
		pip-compile --generate-hashes --resolver=backtracking --upgrade-package all --output-file $(LOCK_FILE) $(REQUIREMENTS_IN); \
	fi
	@echo "✅ Lockfile upgraded! Run 'make sync' to apply."

clean:
	@echo "🧹 Cleaning pip cache & lockfile..."
	rm -f $(LOCK_FILE)
	pip cache purge
	@echo "✅ Cleaned!"
