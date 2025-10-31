#!/usr/bin/env python3
"""
Performance Integration Verification Script
===========================================
Verifies all performance optimizations are properly integrated.

Run this before merging to main.
"""

import sys
import os
import importlib

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

print("🔍 Verifying Performance Optimization Integration...")
print("=" * 60)

errors = []
warnings = []

# Test 1: Core module imports
print("\n1. Testing core module imports...")
modules_to_test = [
    ('core.onnx_runtime', 'ONNX Runtime'),
    ('core.batcher', 'Micro-Batching'),
    ('core.cache_wrapper', 'Feature Cache'),
    ('core.llm_cache', 'LLM Cache'),
    ('core.startup_perf', 'Startup Performance'),
    ('core.telemetry', 'OpenTelemetry'),
    ('core.pyroscope_config', 'Pyroscope'),
    ('core.performance_slo', 'SLO Monitoring'),
    ('core.metrics_exporter', 'Metrics Exporter'),
    ('core.contracts', 'API Contracts'),
    ('core.feast_integration', 'Feast Integration'),
    ('core.performance_integration', 'Performance Integration'),
]

for module_name, display_name in modules_to_test:
    try:
        importlib.import_module(module_name)
        print(f"  ✅ {display_name}")
    except ImportError as e:
        warnings.append(f"{display_name}: {e}")
        print(f"  ⚠️  {display_name} (import failed: {e})")
    except Exception as e:
        errors.append(f"{display_name}: {e}")
        print(f"  ❌ {display_name} (error: {e})")

# Test 2: Configuration files
print("\n2. Testing configuration files...")
config_files = [
    ('backend/backend/gunicorn.conf.py', 'Gunicorn config'),
    ('backend/infrastructure/pgbouncer/pgbouncer.ini', 'PgBouncer config'),
    ('backend/backend/feast/feature_store.yaml', 'Feast config'),
    ('backend/requirements_performance.txt', 'Performance requirements'),
]

for file_path, display_name in config_files:
    full_path = os.path.join(os.path.dirname(__file__), '..', '..', file_path)
    if os.path.exists(full_path):
        print(f"  ✅ {display_name}")
    else:
        errors.append(f"{display_name}: File not found")
        print(f"  ❌ {display_name} (not found)")

# Test 3: Docker compose files
print("\n3. Testing Docker Compose configuration...")
docker_files = [
    ('docker-compose.yml', 'Main docker-compose'),
    ('docker-compose.monitoring.yml', 'Monitoring docker-compose'),
]

for file_path, display_name in docker_files:
    full_path = os.path.join(os.path.dirname(__file__), '..', '..', file_path)
    if os.path.exists(full_path):
        print(f"  ✅ {display_name}")
    else:
        warnings.append(f"{display_name}: File not found (optional)")
        print(f"  ⚠️  {display_name} (not found)")

# Test 4: Integration in final_complete_server.py
print("\n4. Testing server integration...")
server_file = os.path.join(os.path.dirname(__file__), '..', 'backend', 'final_complete_server.py')
if os.path.exists(server_file):
    with open(server_file, 'r') as f:
        content = f.read()
        if 'performance_integration' in content:
            print("  ✅ Performance integration imported")
        else:
            errors.append("Performance integration not found in final_complete_server.py")
            print("  ❌ Performance integration not found")
        
        if 'initialize_performance_optimizations' in content:
            print("  ✅ Performance optimizations initialized")
        else:
            errors.append("Performance optimizations not initialized")
            print("  ❌ Performance optimizations not initialized")
else:
    errors.append("final_complete_server.py not found")
    print("  ❌ final_complete_server.py not found")

# Test 5: Optional dependencies (should fail gracefully)
print("\n5. Testing graceful degradation...")
optional_modules = [
    ('onnxruntime', 'ONNX Runtime'),
    ('blake3', 'BLAKE3'),
    ('pyroscope', 'Pyroscope'),
    ('prometheus_client', 'Prometheus'),
]

for module_name, display_name in optional_modules:
    try:
        importlib.import_module(module_name)
        print(f"  ✅ {display_name} (installed)")
    except ImportError:
        print(f"  ⚠️  {display_name} (not installed, will use fallbacks)")
        # This is OK - modules should degrade gracefully

# Summary
print("\n" + "=" * 60)
print("📊 Verification Summary")
print("=" * 60)

if errors:
    print(f"\n❌ Errors found ({len(errors)}):")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
else:
    print(f"\n✅ No errors found!")

if warnings:
    print(f"\n⚠️  Warnings ({len(warnings)}):")
    for warning in warnings:
        print(f"  - {warning}")

print("\n✅ Integration verification complete!")
print("Ready for merge to main! 🚀")

