#!/usr/bin/env node
/**
 * Test navigation reachability for all new screens
 */

const fs = require('fs');
const path = require('path');

const screens = {
  'PortfolioScreen': {
    file: 'mobile/src/features/portfolio/screens/PortfolioScreen.tsx',
    routes: ['portfolio', 'Portfolio'],
    navigationFiles: [
      'mobile/src/navigation/AppNavigator.tsx',
      'mobile/src/App.tsx',
    ],
  },
  'FamilyManagementModal': {
    file: 'mobile/src/features/family/components/FamilyManagementModal.tsx',
    accessedVia: 'PortfolioScreen (family button)',
    navigationFiles: ['mobile/src/features/portfolio/screens/PortfolioScreen.tsx'],
  },
  'SharedOrb': {
    file: 'mobile/src/features/family/components/SharedOrb.tsx',
    accessedVia: 'PortfolioScreen (when family group exists)',
    navigationFiles: ['mobile/src/features/portfolio/screens/PortfolioScreen.tsx'],
  },
  'PrivacyDashboard': {
    file: 'mobile/src/features/privacy/components/PrivacyDashboard.tsx',
    accessedVia: 'ProfileScreen (settings menu)',
    navigationFiles: ['mobile/src/features/user/screens/ProfileScreen.tsx'],
  },
  'OrbRenderer': {
    file: 'web/src/components/OrbRenderer.tsx',
    accessedVia: 'Web App (main page)',
    navigationFiles: ['web/src/App.tsx'],
  },
};

function checkRoute(navFile, routeName) {
  try {
    const content = fs.readFileSync(navFile, 'utf8');
    // Check for route definition
    const routePattern = new RegExp(
      `name=["']${routeName}["']|name=["']${routeName.toLowerCase()}["']|case ['"]${routeName}['"]|case ['"]${routeName.toLowerCase()}['"]`,
      'i'
    );
    return routePattern.test(content);
  } catch (error) {
    return false;
  }
}

function checkImport(filePath, componentName) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const importPattern = new RegExp(
      `import.*${componentName}|from.*${componentName}`,
      'i'
    );
    return importPattern.test(content);
  } catch (error) {
    return false;
  }
}

function checkUsage(filePath, componentName) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const jsxPattern = new RegExp(`<${componentName}|<\\w+.*${componentName}`, 'i');
    return jsxPattern.test(content);
  } catch (error) {
    return false;
  }
}

console.log('🧭 Testing Navigation Reachability...\n');

const report = {
  reachable: [],
  unreachable: [],
  warnings: [],
};

for (const [screenName, config] of Object.entries(screens)) {
  console.log(`Checking ${screenName}...`);
  
  const filePath = path.join(process.cwd(), config.file);
  if (!fs.existsSync(filePath)) {
    console.log(`  ⚠️  File not found: ${config.file}\n`);
    report.warnings.push({ screen: screenName, reason: 'File not found' });
    continue;
  }
  
  let isReachable = false;
  const reachabilityDetails = [];
  
  // Check routes
  if (config.routes) {
    for (const navFile of config.navigationFiles) {
      const navPath = path.join(process.cwd(), navFile);
      if (fs.existsSync(navPath)) {
        for (const route of config.routes) {
          if (checkRoute(navPath, route)) {
            isReachable = true;
            reachabilityDetails.push(`Route "${route}" in ${path.basename(navFile)}`);
          }
        }
      }
    }
  }
  
  // Check component usage
  if (config.accessedVia) {
    for (const navFile of config.navigationFiles) {
      const navPath = path.join(process.cwd(), navFile);
      if (fs.existsSync(navPath)) {
        if (checkImport(navPath, screenName) || checkUsage(navPath, screenName)) {
          isReachable = true;
          reachabilityDetails.push(`Used in ${path.basename(navFile)}`);
        }
      }
    }
  }
  
  if (isReachable) {
    console.log(`  ✅ Reachable:`);
    reachabilityDetails.forEach(detail => console.log(`     - ${detail}`));
    if (config.accessedVia) {
      console.log(`     - Access: ${config.accessedVia}`);
    }
    console.log();
    report.reachable.push({ screen: screenName, details: reachabilityDetails });
  } else {
    console.log(`  ❌ Not reachable\n`);
    report.unreachable.push({ screen: screenName, file: config.file });
  }
}

console.log('\n📊 Navigation Summary:\n');
console.log(`✅ Reachable: ${report.reachable.length}`);
console.log(`❌ Unreachable: ${report.unreachable.length}`);
console.log(`⚠️  Warnings: ${report.warnings.length}\n`);

if (report.unreachable.length > 0) {
  console.log('❌ Unreachable Screens:\n');
  report.unreachable.forEach(item => {
    console.log(`  - ${item.screen}`);
    console.log(`    File: ${item.file}`);
    console.log();
  });
}

if (report.warnings.length > 0) {
  console.log('⚠️  Warnings:\n');
  report.warnings.forEach(item => {
    console.log(`  - ${item.screen}: ${item.reason}`);
    console.log();
  });
}

// Exit with error code if unreachable screens found
process.exit(report.unreachable.length > 0 ? 1 : 0);

