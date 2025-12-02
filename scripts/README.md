# Scripts Directory

This directory contains all shell scripts organized by purpose.

## Directory Structure

```
scripts/
├── setup/          # Setup and configuration scripts
├── start/          # Startup and run scripts
├── deploy/         # Deployment scripts
├── utils/          # Utility scripts (cleanup, reset, etc.)
├── archive/        # Archive/documentation scripts
└── README.md       # This file
```

## Script Categories

### Setup Scripts (`scripts/setup/`)
Scripts for setting up and configuring the environment, services, and features.

**Examples:**
- `setup_day_trading.sh` - Day trading setup
- `setup_postgres_env.sh` - PostgreSQL environment setup
- `setup_yodlee.sh` - Yodlee integration setup
- `setup_ml_wake_word.sh` - ML wake word setup
- `setup-aws-oidc.sh` - AWS OIDC setup

### Startup Scripts (`scripts/start/`)
Scripts for starting services and applications.

**Examples:**
- `start_backend_now.sh` - Start backend server (main_server.py)
- `start_all_features.sh` - Start all services
- `restart_backend.sh` - Restart backend server
- `start_mobile.sh` - Start mobile app
- `START_LOCAL_DEMO.sh` - Start local demo

### Deployment Scripts (`scripts/deploy/`)
Scripts for deploying to production or staging environments.

**Examples:**
- `deploy_to_production.sh` - Production deployment

### Utility Scripts (`scripts/utils/`)
Utility scripts for maintenance, testing, and operations.

**Examples:**
- `run_tests.sh` - Run test suite
- `run_full_app.sh` - Run full application
- `stop_full_app.sh` - Stop all services
- `rn-reset.sh` - React Native reset utility
- `bootstrap_backend.sh` - Backend bootstrap
- `cleanup_disk_space.sh` - Disk cleanup utility
- `schedule_pre_market_scanner.sh` - Pre-market scanner scheduling

### Archive Scripts (`scripts/archive/`)
Scripts for archiving and organizing documentation/files.

**Examples:**
- `archive_outdated_docs.sh` - Archive outdated documentation
- `archive_more_docs.sh` - Archive additional documentation
- `archive_duplicate_scripts.sh` - Archive duplicate scripts

## Usage

### Running Setup Scripts
```bash
cd scripts/setup
./setup_day_trading.sh
```

### Starting Services
```bash
cd scripts/start
./start_backend_now.sh
```

### Running Utilities
```bash
cd scripts/utils
./run_tests.sh
```

## Important Notes

- **Main Backend Startup**: Use `scripts/start/start_backend_now.sh` (uses `main_server.py`)
- **All Services**: Use `scripts/start/start_all_features.sh` to start everything
- **Tests**: Use `scripts/utils/run_tests.sh` to run all tests

## Script Locations

Some scripts remain in their original locations:
- `main_server.py` - Main backend server (root)
- Django test scripts - In `deployment_package/backend/`
- Mobile scripts - In `mobile/` directory
- Test scripts - In `tests/scripts/`

