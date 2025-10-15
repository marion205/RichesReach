# Files to Remove - RichesReach Cleanup

## 🗑️ Files You Can Safely Remove

### 1. **Old Task Definition Files** (40+ files)
These are outdated ECS task definitions that have been replaced by the optimized versions:
- `aws-task-definition-*.json` (8 files)
- `td-*.json` (40+ numbered files)
- `ecs-task-definition-with-secrets.json`
- `final_*.json` (3 files)
- `fixed_*.json` (2 files)
- `production_task_def.json`
- `simple-task-definition.json`
- `updated_td.json`

### 2. **Old Deployment Scripts** (20+ files)
These are outdated deployment scripts:
- `deploy_*.sh` (15+ files)
- `deploy-*.sh` (3 files)
- `quick_*.sh` (2 files)
- `hot-swap-service.sh`
- `start_hotfix.sh`
- `update-ecs-with-new-image.sh`
- `wait-for-images.sh`

### 3. **Old Configuration Files** (10+ files)
- `enhanced_producer_config.json.bak`
- `new_secret.json`
- `updated_secret.json`
- `updated_richesreach_policy.json`
- `production_deployment_config.*`
- `production_environment_config.json`
- `phase3_config.py`
- `phase3.env.template`

### 4. **Old Test Files and Reports** (30+ files)
- `benchmark_*.py` (2 files)
- `competitive_analysis_*.py` (2 files)
- `core_test_results.json`
- `phase3_test_results.json`
- `fix_ml_r2_simple.py`
- `improve_ml_r2_score.py`
- `train_improved_models.py`
- `performance_dashboard.py`
- `performance_report_*.json` (15+ files)
- `test_*.py` (25+ files)
- `test_*.json` (10+ files)
- `test-*.sh` (2 files)

### 5. **Old Setup and Configuration Files** (20+ files)
- `check_*.py` (2 files)
- `create_*.json` (5 files)
- `create_*.sql`
- `grant_schema_permissions.json`
- `simple_db_setup.json`
- `populate_stocks_task.json`
- `setup_*.py` (4 files)
- `setup-*.sh` (4 files)
- `set-password.sh`
- `rotate_secrets_manual.sh`
- `run-migration-fix.sh`
- `monitor-*.sh` (2 files)
- `health_check_phase3.py`
- `compare_deployment_speed.sh`

### 6. **Old Documentation Files** (30+ files)
- `ADVANCED_*.md` (2 files)
- `AI_SCANS_*.md` (2 files)
- `BACKEND_TEST_RESULTS.md`
- `BACKTESTING_*.md`
- `BRANCHING_STRATEGY.md`
- `DEPLOYMENT_*.md` (3 files)
- `DEVELOPMENT_SETUP.md`
- `ENTERPRISE_*.md` (2 files)
- `FINAL_DEPLOYMENT_*.md`
- `HOTSPOT_*.md`
- `HYBRID_*.md` (2 files)
- `LEGAL_DISCLAIMERS.md`
- `ML_*.md` (2 files)
- `MULTI_REGION_*.md`
- `NAVIGATION_*.md`
- `NETWORK_SETUP.md`
- `NEXT_WEEK_*.md`
- `OPENAI_*.md`
- `PERFORMANCE_*.md`
- `PHASE_*.md` (4 files)
- `PRODUCTION_*.md` (2 files)
- `RISK_COACH_*.md`
- `RUNBOOK.md`
- `SECRET_*.md` (2 files)
- `SECURE_*.md` (2 files)
- `SECURITY_GUIDE.md`
- `SEPOLIA_*.md` (3 files)
- `SWING_TRADING_*.md`
- `TEST_NEW_FEATURES.md`
- `UI_TESTING_*.md`

### 7. **Old Log Files** (3 files)
- `django_server.log`
- `django.log`
- `server.log`

### 8. **Old Database Files** (1 file)
- `trading_outcomes.db`

### 9. **Old Trigger Files** (4 files)
- `migration-trigger.txt`
- `trigger-build.txt`
- `trigger-oidc.txt`
- `trigger-websocket-fix.txt`

### 10. **Old Verification Files** (3 files)
- `verify_secrets_deployment.sh`
- `verify-aws-setup.sh`
- `verify-deployment.sh`

### 11. **Old Test Documentation** (2 files)
- `test-oidc-fresh.md`
- `test-oidc.md`

### 12. **Old Simple Server Files** (2 files)
- `aws-server.py`
- `simple_test_server.py`

## ✅ Files to Keep (Essential)

### **Current Deployment Files**
- `ecs_task_definition_simple.json` (current)
- `ecs_task_definition_optimized.json` (new optimized version)

### **Optimized Dockerfiles**
- `Dockerfile.streaming.optimized`
- `backend/Dockerfile.optimized`
- `rust_crypto_engine/Dockerfile.optimized`

### **Optimization Scripts**
- `cleanup_docker.sh`
- `build_optimized.sh`
- `cleanup_files.sh` (this cleanup script)

### **Documentation**
- `DOCKER_OPTIMIZATION_GUIDE.md`
- `README.md`

### **Docker Ignore Files**
- `.dockerignore`
- `backend/.dockerignore`
- `rust_crypto_engine/.dockerignore`

### **Core Application Files**
- `main.py`
- `requirements.streaming.txt`
- `docker-compose.yml`
- All files in `backend/`, `rust_crypto_engine/`, `mobile/`, `ios/`, `infrastructure/`, `scripts/`, `tests/`, `docs/`, `assets/`, `models/`, `monitoring/`, `nginx/`, `deployment/`, `deployment_package/`

## 🚀 How to Clean Up

### Option 1: Automated Cleanup (Recommended)
```bash
./cleanup_files.sh
```

### Option 2: Manual Cleanup
Remove the files listed above manually.

## 📊 Expected Results

After cleanup, you should have:
- **~200+ fewer files** in your project root
- **Much cleaner project structure**
- **Easier navigation and maintenance**
- **Reduced confusion about which files to use**
- **Faster git operations**

## ⚠️ Important Notes

1. **Backup First**: Make sure you have a backup before running the cleanup
2. **Review**: The cleanup script will ask for confirmation before proceeding
3. **Essential Files**: Only non-essential files are removed
4. **Current Deployment**: Your current deployment files are preserved
5. **Optimized Versions**: New optimized files are kept

## 🎯 Next Steps After Cleanup

1. **Test the optimized build**:
   ```bash
   ./build_optimized.sh
   ```

2. **Clean up Docker**:
   ```bash
   ./cleanup_docker.sh
   ```

3. **Deploy with optimized configuration**:
   Use `ecs_task_definition_optimized.json` for deployment

4. **Commit the cleaned project**:
   ```bash
   git add .
   git commit -m "Clean up redundant files and add Docker optimizations"
   git push
   ```
