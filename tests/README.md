# Tests Directory

This directory contains all test files organized by type and location.

## Directory Structure

```
tests/
├── root_tests/          # Test files moved from repository root
├── scripts/             # Test shell scripts and utilities
├── unit/                # Unit tests
├── integration/         # Integration tests
└── README.md           # This file
```

## Test File Locations

### Root Tests (`tests/root_tests/`)
Test files that were originally in the repository root. These are standalone test scripts that can be run independently.

**Python Test Files:**
- `test_*.py` - Various test scripts
- `backtest_*.py` - Backtesting scripts
- `system_test_*.py` - System-level tests
- `run_day_trading_tests.py` - Day trading test runner

### Test Scripts (`tests/scripts/`)
Shell scripts and utilities for running tests and verification.

**Shell Scripts:**
- `test_*.sh` - Test execution scripts
- `TEST_*.sh` - Production endpoint tests
- `verify_*.sh` - Verification scripts

**JavaScript Files:**
- `verify_*.js` - JavaScript verification utilities
- `test_navigation_reachability.js` - Navigation testing

### Unit Tests (`tests/unit/`)
Unit tests for individual components and services.

### Integration Tests (`tests/integration/`)
Integration tests for API endpoints and system integration.

## Django Tests

Django-specific tests remain in their original locations:
- `deployment_package/backend/core/tests/` - Django app tests
- `deployment_package/backend/tests/` - Backend tests

These should not be moved as they're part of the Django app structure.

## Running Tests

### Run all root tests:
```bash
cd tests/root_tests
python3 test_*.py
```

### Run test scripts:
```bash
cd tests/scripts
./test_*.sh
```

### Run Django tests:
```bash
cd deployment_package/backend
python manage.py test
```

### Run all tests:
```bash
./run_tests.sh
```

## Notes

- Test files in `deployment_package/backend/core/tests/` are part of the Django app and should remain there
- Mobile and web test files remain in their respective project directories
- Test files in `node_modules/` and `venv/` are dependencies and should not be moved

