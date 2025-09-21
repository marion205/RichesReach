#!/usr/bin/env python3
"""
Comprehensive script to fix all import paths after file reorganization
"""
import os
import re
import glob

def fix_imports_in_file(file_path):
    """Fix import paths in a single file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix relative path depth issues
    # If we're in features/X/screens/, we need to go up 3 levels to reach mobile root
    if '/features/' in file_path and '/screens/' in file_path:
        content = re.sub(r"from '\.\./", "from '../../../", content)
        content = re.sub(r"from '\./", "from '../../", content)
    elif '/features/' in file_path and '/components/' in file_path:
        content = re.sub(r"from '\.\./", "from '../../../", content)
        content = re.sub(r"from '\./", "from '../../", content)
    elif '/features/' in file_path and '/services/' in file_path:
        content = re.sub(r"from '\.\./", "from '../../../", content)
        content = re.sub(r"from '\./", "from '../../", content)
    
    # Fix specific component imports that moved to features
    component_mappings = {
        'PortfolioGraph': 'features/portfolio/components/PortfolioGraph',
        'PortfolioHoldings': 'features/portfolio/components/PortfolioHoldings',
        'PortfolioComparison': 'features/portfolio/components/PortfolioComparison',
        'StockChart': 'features/stocks/components/StockChart',
        'WatchlistCard': 'features/stocks/components/WatchlistCard',
        'FinancialNews': 'features/stocks/components/FinancialNews',
        'TickerAutocomplete': 'features/stocks/components/TickerAutocomplete',
        'TickerChips': 'features/stocks/components/TickerChips',
        'TickerFollowButton': 'features/stocks/components/TickerFollowButton',
        'SocialFeed': 'features/social/components/SocialFeed',
        'PostCard': 'features/social/components/PostCard',
        'UserProfileCard': 'features/social/components/UserProfileCard',
        'PasswordStrengthIndicator': 'features/auth/components/PasswordStrengthIndicator',
        'OptionChainCard': 'features/options/components/OptionChainCard',
    }
    
    for component, new_path in component_mappings.items():
        # Fix imports like: from '../components/ComponentName'
        pattern = rf"from '\.\./components/{component}'"
        replacement = f"from '../{new_path}'"
        content = re.sub(pattern, replacement, content)
        
        # Fix imports like: from '../../components/ComponentName'
        pattern = rf"from '\.\./\.\./components/{component}'"
        replacement = f"from '../{new_path}'"
        content = re.sub(pattern, replacement, content)
    
    # Fix service imports that moved to features
    service_mappings = {
        'RealTimePortfolioService': 'features/portfolio/services/RealTimePortfolioService',
        'RebalancingStorageService': 'features/portfolio/services/RebalancingStorageService',
        'MarketDataService': 'features/stocks/services/MarketDataService',
        'PriceAlertService': 'features/stocks/services/PriceAlertService',
        'IntelligentPriceAlertService': 'features/stocks/services/IntelligentPriceAlertService',
        'ExpoGoCompatiblePriceAlertService': 'features/stocks/services/ExpoGoCompatiblePriceAlertService',
        'UserProfileService': 'features/user/services/UserProfileService',
        'JWTAuthService': 'features/auth/services/JWTAuthService',
        'AIOptionsService': 'features/options/services/AIOptionsService',
        'PushNotificationService': 'features/notifications/services/PushNotificationService',
        'ExpoGoCompatibleNotificationService': 'features/notifications/services/ExpoGoCompatibleNotificationService',
    }
    
    for service, new_path in service_mappings.items():
        # Fix imports like: from '../services/ServiceName'
        pattern = rf"from '\.\./services/{service}'"
        replacement = f"from '../{new_path}'"
        content = re.sub(pattern, replacement, content)
        
        # Fix imports like: from '../../services/ServiceName'
        pattern = rf"from '\.\./\.\./services/{service}'"
        replacement = f"from '../{new_path}'"
        content = re.sub(pattern, replacement, content)
    
    # Fix screen imports that moved to features
    screen_mappings = {
        'StockScreen': 'features/stocks/screens/StockScreen',
        'TradingScreen': 'features/stocks/screens/TradingScreen',
        'ResearchScreen': 'features/stocks/screens/ResearchScreen',
        'PortfolioScreen': 'features/portfolio/screens/PortfolioScreen',
        'AIPortfolioScreen': 'features/portfolio/screens/AIPortfolioScreen',
        'PortfolioManagementScreen': 'features/portfolio/screens/PortfolioManagementScreen',
        'UserPortfoliosScreen': 'features/portfolio/screens/UserPortfoliosScreen',
        'SocialScreen': 'features/social/screens/SocialScreen',
        'MessageScreen': 'features/social/screens/MessageScreen',
        'DiscoverUsersScreen': 'features/social/screens/DiscoverUsersScreen',
        'UserActivityScreen': 'features/social/screens/UserActivityScreen',
        'LoginScreen': 'features/auth/screens/LoginScreen',
        'SignUpScreen': 'features/auth/screens/SignUpScreen',
        'ForgotPasswordScreen': 'features/auth/screens/ForgotPasswordScreen',
        'OnboardingScreen': 'features/auth/screens/OnboardingScreen',
        'ProfileScreen': 'features/user/screens/ProfileScreen',
        'UserProfileScreen': 'features/user/screens/UserProfileScreen',
        'AccountManagementScreen': 'features/user/screens/AccountManagementScreen',
        'BankAccountScreen': 'features/user/screens/BankAccountScreen',
        'SubscriptionScreen': 'features/user/screens/SubscriptionScreen',
        'AIOptionsScreen': 'features/options/screens/AIOptionsScreen',
        'OptionsLearningScreen': 'features/options/screens/OptionsLearningScreen',
        'LearningPathsScreen': 'features/learning/screens/LearningPathsScreen',
        'PortfolioLearningScreen': 'features/learning/screens/PortfolioLearningScreen',
        'SBLOCLearningScreen': 'features/learning/screens/SBLOCLearningScreen',
        'NotificationsScreen': 'features/notifications/screens/NotificationsScreen',
    }
    
    for screen, new_path in screen_mappings.items():
        # Fix imports like: from '../screens/ScreenName'
        pattern = rf"from '\.\./screens/{screen}'"
        replacement = f"from '../{new_path}'"
        content = re.sub(pattern, replacement, content)
        
        # Fix imports like: from '../../screens/ScreenName'
        pattern = rf"from '\.\./\.\./screens/{screen}'"
        replacement = f"from '../{new_path}'"
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
            if 'node_modules' in file_path or 'fix_' in file_path:
                continue
            if fix_imports_in_file(file_path):
                files_updated += 1
    
    print(f"Updated {files_updated} files")

if __name__ == "__main__":
    main()
