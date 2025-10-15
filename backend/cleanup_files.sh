#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to safely remove files
safe_remove() {
    local file="$1"
    if [[ -f "$file" ]]; then
        rm "$file"
        print_success "Removed: $file"
    else
        print_warning "File not found: $file"
    fi
}

# Function to safely remove directories
safe_remove_dir() {
    local dir="$1"
    if [[ -d "$dir" ]]; then
        rm -rf "$dir"
        print_success "Removed directory: $dir"
    else
        print_warning "Directory not found: $dir"
    fi
}

main() {
    echo "=========================================="
    echo "🧹 RichesReach File Cleanup Script"
    echo "=========================================="
    echo

    print_status "Starting file cleanup process..."
    echo

    # Ask for confirmation
    print_warning "This will remove many redundant and outdated files."
    print_warning "Make sure you have a backup if needed."
    echo
    read -p "Do you want to proceed with cleanup? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cleanup cancelled by user."
        exit 0
    fi

    echo

    # 1. Remove old task definition files (keep only the optimized ones)
    print_status "=== Removing old task definition files ==="
    safe_remove "aws-task-definition-final.json"
    safe_remove "aws-task-definition-fixed-binding.json"
    safe_remove "aws-task-definition-fixed-container.json"
    safe_remove "aws-task-definition-fixed-network.json"
    safe_remove "aws-task-definition-fixed.json"
    safe_remove "aws-task-definition-simple.json"
    safe_remove "aws-task-definition-with-openai.json"
    safe_remove "aws-task-definition.json"
    safe_remove "auto_adopt_task_def.json"
    safe_remove "corrected_task_def.json"
    safe_remove "current_task_def.json"
    safe_remove "current_td.json"
    safe_remove "ecs-task-definition-with-secrets.json"
    safe_remove "final_fixed_task_def.json"
    safe_remove "final_secret.json"
    safe_remove "final_task_def.json"
    safe_remove "fixed_task_def_v2.json"
    safe_remove "fixed_task_def.json"
    safe_remove "production_task_def.json"
    safe_remove "simple-task-definition.json"
    safe_remove "updated_td.json"

    # Remove numbered task definition files
    for i in {139..178}; do
        safe_remove "td-${i}.json"
        safe_remove "td-${i}-base.json"
        safe_remove "td-${i}-clean.json"
        safe_remove "td-${i}-stripped.json"
    done
    safe_remove "td195.json"
    safe_remove "td201.json"
    safe_remove "td202.json"
    safe_remove "td202_clean.json"
    safe_remove "td202_final.json"
    safe_remove "td202_fixed.json"
    safe_remove "td206-diagnostic.json"

    echo

    # 2. Remove old deployment scripts (keep only the essential ones)
    print_status "=== Removing old deployment scripts ==="
    safe_remove "deploy_fast.sh"
    safe_remove "deploy_fixed.sh"
    safe_remove "deploy_multi_region.sh"
    safe_remove "deploy_other_regions.sh"
    safe_remove "deploy_phase2.sh"
    safe_remove "deploy_phase3.sh"
    safe_remove "deploy_production_clean.sh"
    safe_remove "deploy_secure_secrets.sh"
    safe_remove "deploy_signals_api.sh"
    safe_remove "deploy_signals_only.sh"
    safe_remove "deploy_simple.sh"
    safe_remove "deploy_streaming_pipeline.sh"
    safe_remove "deploy_to_aws.sh"
    safe_remove "deploy_without_docker.sh"
    safe_remove "deploy-aws-secure.sh"
    safe_remove "deploy-clean-image.sh"
    safe_remove "deploy-with-digest.sh"
    safe_remove "quick_deploy_latest.sh"
    safe_remove "quick_start_sepolia.sh"
    safe_remove "quick-status.sh"
    safe_remove "hot-swap-service.sh"
    safe_remove "start_hotfix.sh"
    safe_remove "update-ecs-with-new-image.sh"
    safe_remove "wait-for-images.sh"

    echo

    # 3. Remove old configuration files
    print_status "=== Removing old configuration files ==="
    safe_remove "enhanced_producer_config.json.bak"
    safe_remove "new_secret.json"
    safe_remove "updated_secret.json"
    safe_remove "updated_richesreach_policy.json"
    safe_remove "production_deployment_config.json"
    safe_remove "production_deployment_config.py"
    safe_remove "production_environment_config.json"
    safe_remove "phase3_config.py"
    safe_remove "phase3.env.template"

    echo

    # 4. Remove old test files and reports
    print_status "=== Removing old test files and reports ==="
    safe_remove "benchmark_results.json"
    safe_remove "benchmark_test_suite.py"
    safe_remove "competitive_analysis_report.json"
    safe_remove "competitive_analysis_report.py"
    safe_remove "core_test_results.json"
    safe_remove "phase3_test_results.json"
    safe_remove "fix_ml_r2_simple.py"
    safe_remove "improve_ml_r2_score.py"
    safe_remove "train_improved_models.py"
    safe_remove "performance_dashboard.py"

    # Remove performance reports
    for file in performance_report_*.json; do
        safe_remove "$file"
    done

    echo

    # 5. Remove old test files
    print_status "=== Removing old test files ==="
    safe_remove "test_6m_timeframe.py"
    safe_remove "test_ai_scans_integration.py"
    safe_remove "test_all_benchmarks.py"
    safe_remove "test_all_endpoints.py"
    safe_remove "test_all_ui_endpoints.py"
    safe_remove "test_app_config.js"
    safe_remove "test_appdb_connection.json"
    safe_remove "test_appuser_postgres.json"
    safe_remove "test_benchmark_data.py"
    safe_remove "test_complete_streaming_pipeline.py"
    safe_remove "test_core_functionality.py"
    safe_remove "test_db_connection.json"
    safe_remove "test_graphql_queries.py"
    safe_remove "test_kinesis_stream.py"
    safe_remove "test_middleware.py"
    safe_remove "test_minimal_server.py"
    safe_remove "test_new_appuser.json"
    safe_remove "test_phase2_endpoints.py"
    safe_remove "test_phase2_minimal.py"
    safe_remove "test_phase3_comprehensive.py"
    safe_remove "test_phase3_offline.py"
    safe_remove "test_phase3.py"
    safe_remove "test_portfolio_comparison_integration.py"
    safe_remove "test_richesreach_db.json"
    safe_remove "test_sepolia_config.py"
    safe_remove "test_simple_server.py"
    safe_remove "test_swing_trading_comprehensive.py"
    safe_remove "test-crypto-ui.sh"
    safe_remove "test-dockerfile"

    echo

    # 6. Remove old setup and configuration files
    print_status "=== Removing old setup files ==="
    safe_remove "check_dependencies.py"
    safe_remove "check_permissions.json"
    safe_remove "create_appdb_with_appuser.json"
    safe_remove "create_appdb.json"
    safe_remove "create_appuser.json"
    safe_remove "create_appuser.sql"
    safe_remove "create_db_user.json"
    safe_remove "grant_schema_permissions.json"
    safe_remove "simple_db_setup.json"
    safe_remove "populate_stocks_task.json"
    safe_remove "setup_live_data_feeds.py"
    safe_remove "setup_live_data_feeds_with_secrets.py"
    safe_remove "setup_ml_model_integration.py"
    safe_remove "setup_streaming_permissions.py"
    safe_remove "setup-aws-oidc.sh"
    safe_remove "setup-aws-roles.sh"
    safe_remove "setup-aws-secrets.sh"
    safe_remove "setup-local-env.sh"
    safe_remove "set-password.sh"
    safe_remove "rotate_secrets_manual.sh"
    safe_remove "run-migration-fix.sh"
    safe_remove "monitor-oidc-run.sh"
    safe_remove "monitor_streaming_pipeline.py"
    safe_remove "health_check_phase3.py"
    safe_remove "compare_deployment_speed.sh"

    echo

    # 7. Remove old documentation files (keep only the essential ones)
    print_status "=== Removing old documentation files ==="
    safe_remove "ADVANCED_AI_INTEGRATION.md"
    safe_remove "ADVANCED_SECURITY.md"
    safe_remove "AI_SCANS_OPTIONS_COPILOT_IMPLEMENTATION.md"
    safe_remove "AI_SCANS_OPTIONS_NAVIGATION_GUIDE.md"
    safe_remove "BACKEND_TEST_RESULTS.md"
    safe_remove "BACKTESTING_SCREEN_UPGRADE.md"
    safe_remove "BRANCHING_STRATEGY.md"
    safe_remove "DEPLOYMENT_READINESS_REPORT.md"
    safe_remove "DEPLOYMENT_RUNBOOK.md"
    safe_remove "DEPLOYMENT_STATUS.md"
    safe_remove "DEVELOPMENT_SETUP.md"
    safe_remove "ENTERPRISE_ENGINEERING_CHECKLIST.md"
    safe_remove "ENTERPRISE_UPGRADE_SUMMARY.md"
    safe_remove "FINAL_DEPLOYMENT_READINESS_REPORT.md"
    safe_remove "HOTSPOT_TROUBLESHOOTING.md"
    safe_remove "HYBRID_COMPLETE_SUMMARY.md"
    safe_remove "HYBRID_SETUP_GUIDE.md"
    safe_remove "LEGAL_DISCLAIMERS.md"
    safe_remove "ML_MODULE_UPGRADE.md"
    safe_remove "ML_TRAINING_SUCCESS.md"
    safe_remove "MULTI_REGION_DEPLOYMENT.md"
    safe_remove "NAVIGATION_FLOW_DIAGRAM.md"
    safe_remove "NETWORK_SETUP.md"
    safe_remove "NEXT_WEEK_PACK_SETUP.md"
    safe_remove "OPENAI_DEPLOYMENT_GUIDE.md"
    safe_remove "PERFORMANCE_OPTIMIZATION.md"
    safe_remove "PHASE_1_ARCHITECTURE_UPGRADE.md"
    safe_remove "PHASE_2_ARCHITECTURE_UPGRADE.md"
    safe_remove "PHASE_3_ARCHITECTURE_UPGRADE.md"
    safe_remove "PHASE_3_DEPLOYMENT_GUIDE.md"
    safe_remove "PRODUCTION_SETUP_COMPLETE.md"
    safe_remove "PRODUCTION_SETUP.md"
    safe_remove "RISK_COACH_SCREEN_UPGRADE.md"
    safe_remove "RUNBOOK.md"
    safe_remove "SECRET_ROTATION_GUIDE.md"
    safe_remove "SECURE_KEY_MANAGEMENT_TEMPLATE.md"
    safe_remove "SECURE_SECRETS_ROTATION_TEMPLATE.md"
    safe_remove "SECURITY_GUIDE.md"
    safe_remove "SEPOLIA_IMPLEMENTATION_SUMMARY.md"
    safe_remove "SEPOLIA_READY_TO_TEST.md"
    safe_remove "SEPOLIA_SETUP_GUIDE.md"
    safe_remove "SWING_TRADING_IMPLEMENTATION.md"
    safe_remove "TEST_NEW_FEATURES.md"
    safe_remove "UI_TESTING_GUIDE.md"

    echo

    # 8. Remove old log files
    print_status "=== Removing old log files ==="
    safe_remove "django_server.log"
    safe_remove "django.log"
    safe_remove "server.log"

    echo

    # 9. Remove old database files
    print_status "=== Removing old database files ==="
    safe_remove "trading_outcomes.db"

    echo

    # 10. Remove old trigger files
    print_status "=== Removing old trigger files ==="
    safe_remove "migration-trigger.txt"
    safe_remove "trigger-build.txt"
    safe_remove "trigger-oidc.txt"
    safe_remove "trigger-websocket-fix.txt"

    echo

    # 11. Remove old verification files
    print_status "=== Removing old verification files ==="
    safe_remove "verify_secrets_deployment.sh"
    safe_remove "verify-aws-setup.sh"
    safe_remove "verify-deployment.sh"

    echo

    # 12. Remove old test documentation
    print_status "=== Removing old test documentation ==="
    safe_remove "test-oidc-fresh.md"
    safe_remove "test-oidc.md"

    echo

    # 13. Remove old simple server files
    print_status "=== Removing old simple server files ==="
    safe_remove "aws-server.py"
    safe_remove "simple_test_server.py"

    echo

    print_success "🎉 File cleanup completed successfully!"
    print_status "Removed redundant and outdated files to clean up your project."
    echo
    print_status "Files kept (essential for current deployment):"
    echo "  ✅ ecs_task_definition_simple.json (current)"
    echo "  ✅ ecs_task_definition_optimized.json (new optimized version)"
    echo "  ✅ Dockerfile.streaming.optimized (new optimized version)"
    echo "  ✅ backend/Dockerfile.optimized (new optimized version)"
    echo "  ✅ rust_crypto_engine/Dockerfile.optimized (new optimized version)"
    echo "  ✅ cleanup_docker.sh (Docker cleanup script)"
    echo "  ✅ build_optimized.sh (optimized build script)"
    echo "  ✅ DOCKER_OPTIMIZATION_GUIDE.md (documentation)"
    echo "  ✅ All .dockerignore files"
    echo
    print_status "Your project is now much cleaner and ready for deployment!"
}

# Run the main function
main "$@"
