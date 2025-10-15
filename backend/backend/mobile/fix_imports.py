#!/usr/bin/env python3
"""
Script to fix import paths after file reorganization
"""
import os
import re
import glob

def fix_imports_in_file(file_path):
    """Fix import paths in a single file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Define import path mappings
    mappings = [
        # Screens
        (r"from '\.\./screens/", "from '../../screens/"),
        (r"from '\./screens/", "from '../screens/"),
        (r"from '\.\./\.\./screens/", "from '../../../screens/"),
        
        # Components - old paths to new feature paths
        (r"from '\.\./components/PortfolioGraph'", "from '../features/portfolio/components/PortfolioGraph'"),
        (r"from '\.\./components/PortfolioHoldings'", "from '../features/portfolio/components/PortfolioHoldings'"),
        (r"from '\.\./components/PortfolioComparison'", "from '../features/portfolio/components/PortfolioComparison'"),
        (r"from '\.\./components/StockChart'", "from '../features/stocks/components/StockChart'"),
        (r"from '\.\./components/WatchlistCard'", "from '../features/stocks/components/WatchlistCard'"),
        (r"from '\.\./components/FinancialNews'", "from '../features/stocks/components/FinancialNews'"),
        (r"from '\.\./components/TickerAutocomplete'", "from '../features/stocks/components/TickerAutocomplete'"),
        (r"from '\.\./components/TickerChips'", "from '../features/stocks/components/TickerChips'"),
        (r"from '\.\./components/TickerFollowButton'", "from '../features/stocks/components/TickerFollowButton'"),
        (r"from '\.\./components/SocialFeed'", "from '../features/social/components/SocialFeed'"),
        (r"from '\.\./components/PostCard'", "from '../features/social/components/PostCard'"),
        (r"from '\.\./components/UserProfileCard'", "from '../features/social/components/UserProfileCard'"),
        (r"from '\.\./components/PasswordStrengthIndicator'", "from '../features/auth/components/PasswordStrengthIndicator'"),
        
        # Services - old paths to new feature paths
        (r"from '\.\./services/RealTimePortfolioService'", "from '../features/portfolio/services/RealTimePortfolioService'"),
        (r"from '\.\./services/RebalancingStorageService'", "from '../features/portfolio/services/RebalancingStorageService'"),
        (r"from '\.\./services/MarketDataService'", "from '../features/stocks/services/MarketDataService'"),
        (r"from '\.\./services/PriceAlertService'", "from '../features/stocks/services/PriceAlertService'"),
        (r"from '\.\./services/IntelligentPriceAlertService'", "from '../features/stocks/services/IntelligentPriceAlertService'"),
        (r"from '\.\./services/ExpoGoCompatiblePriceAlertService'", "from '../features/stocks/services/ExpoGoCompatiblePriceAlertService'"),
        (r"from '\.\./services/UserProfileService'", "from '../features/user/services/UserProfileService'"),
        (r"from '\.\./services/JWTAuthService'", "from '../features/auth/services/JWTAuthService'"),
        (r"from '\.\./services/AIOptionsService'", "from '../features/options/services/AIOptionsService'"),
        (r"from '\.\./services/PushNotificationService'", "from '../features/notifications/services/PushNotificationService'"),
        (r"from '\.\./services/ExpoGoCompatibleNotificationService'", "from '../features/notifications/services/ExpoGoCompatibleNotificationService'"),
        
        # Fix relative paths within features
        (r"from '\.\./\.\./components/", "from '../../components/"),
        (r"from '\.\./\.\./services/", "from '../../services/"),
        (r"from '\.\./\.\./screens/", "from '../../screens/"),
        (r"from '\.\./\.\./constants'", "from '../../constants"),
        (r"from '\.\./\.\./hooks/", "from '../../hooks/"),
    ]
    
    # Apply mappings
    for pattern, replacement in mappings:
        content = re.sub(pattern, replacement, content)
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {file_path}")
        return True
    return False

def main():
    """Main function to fix all import paths"""
    # Find all TypeScript/JavaScript files
    patterns = [
        'mobile/**/*.tsx',
        'mobile/**/*.ts',
    ]
    
    files_updated = 0
    for pattern in patterns:
        for file_path in glob.glob(pattern, recursive=True):
            if 'node_modules' in file_path:
                continue
            if fix_imports_in_file(file_path):
                files_updated += 1
    
    print(f"Updated {files_updated} files")

if __name__ == "__main__":
    main()
