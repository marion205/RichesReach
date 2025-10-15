#!/bin/bash
# Revert Performance Optimizations Script
echo " Reverting Performance Optimizations"
echo "====================================="
# Restore original files
echo " Restoring original files..."
cp screens/HomeScreen.tsx.backup screens/HomeScreen.tsx
cp App.tsx.backup App.tsx
# Remove optimization files
echo " Cleaning up optimization files..."
rm -f screens/OptimizedHomeScreen.tsx
rm -f services/PerformanceOptimizationService.ts
rm -f services/OptimizedMarketDataService.ts
rm -f components/PerformanceMonitor.tsx
rm -f config/performance.ts
echo " Reverted to original version!"
echo ""
echo " To restart with original performance:"
echo " npm run start"
