#!/usr/bin/env node
/**
 * Script to verify all new components are being used and reachable
 */

const fs = require('fs');
const path = require('path');

const components = {
  // Family Sharing
  'SharedOrb': {
    file: 'mobile/src/features/family/components/SharedOrb.tsx',
    expectedUsage: ['PortfolioScreen'],
  },
  'FamilyManagementModal': {
    file: 'mobile/src/features/family/components/FamilyManagementModal.tsx',
    expectedUsage: ['PortfolioScreen'],
  },
  'FamilySharingService': {
    file: 'mobile/src/features/family/services/FamilySharingService.ts',
    expectedUsage: ['SharedOrb', 'FamilyManagementModal', 'PortfolioScreen'],
  },
  'FamilyWebSocketService': {
    file: 'mobile/src/features/family/services/FamilyWebSocketService.ts',
    expectedUsage: ['SharedOrb'],
  },
  
  // Privacy
  'PrivacyDashboard': {
    file: 'mobile/src/features/privacy/components/PrivacyDashboard.tsx',
    expectedUsage: ['ProfileScreen', 'Settings'],
  },
  
  // Web
  'OrbRenderer': {
    file: 'web/src/components/OrbRenderer.tsx',
    expectedUsage: ['web/src/App.tsx'],
  },
};

function findImports(filePath, componentName) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const importPattern = new RegExp(
      `import.*${componentName}.*from|from.*${componentName}|require.*${componentName}`,
      'i'
    );
    return importPattern.test(content);
  } catch (error) {
    return false;
  }
}

function findUsage(filePath, componentName) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    // Check for JSX usage
    const jsxPattern = new RegExp(`<${componentName}|<\\w+.*${componentName}`, 'i');
    // Check for function calls
    const callPattern = new RegExp(`${componentName}\\(|${componentName}\\.`, 'i');
    return jsxPattern.test(content) || callPattern.test(content);
  } catch (error) {
    return false;
  }
}

function scanDirectory(dir, componentName) {
  const results = [];
  
  function scan(currentDir) {
    try {
      const files = fs.readdirSync(currentDir);
      
      for (const file of files) {
        const filePath = path.join(currentDir, file);
        const stat = fs.statSync(filePath);
        
        if (stat.isDirectory()) {
          // Skip node_modules and build directories
          if (!['node_modules', '.git', 'build', 'dist', '.next'].includes(file)) {
            scan(filePath);
          }
        } else if (file.endsWith('.tsx') || file.endsWith('.ts') || file.endsWith('.jsx') || file.endsWith('.js')) {
          if (findImports(filePath, componentName) || findUsage(filePath, componentName)) {
            results.push(filePath);
          }
        }
      }
    } catch (error) {
      // Skip directories we can't read
    }
  }
  
  scan(dir);
  return results;
}

console.log('🔍 Scanning for component usage...\n');

const report = {
  used: [],
  unused: [],
  partiallyUsed: [],
};

for (const [componentName, config] of Object.entries(components)) {
  console.log(`Checking ${componentName}...`);
  
  const filePath = path.join(process.cwd(), config.file);
  if (!fs.existsSync(filePath)) {
    console.log(`  ⚠️  File not found: ${config.file}\n`);
    report.unused.push({ component: componentName, reason: 'File not found' });
    continue;
  }
  
  // Search in mobile/src for mobile components
  const searchDir = config.file.startsWith('web/') 
    ? path.join(process.cwd(), 'web/src')
    : path.join(process.cwd(), 'mobile/src');
  
  const usages = scanDirectory(searchDir, componentName);
  
  // Filter out the component file itself
  const externalUsages = usages.filter(u => !u.includes(config.file));
  
  if (externalUsages.length === 0) {
    console.log(`  ❌ Not used anywhere\n`);
    report.unused.push({ 
      component: componentName, 
      reason: 'No imports or usage found',
      file: config.file 
    });
  } else {
    console.log(`  ✅ Used in ${externalUsages.length} file(s):`);
    externalUsages.forEach(u => {
      const relative = path.relative(process.cwd(), u);
      console.log(`     - ${relative}`);
    });
    console.log();
    report.used.push({ component: componentName, usages: externalUsages });
  }
}

console.log('\n📊 Summary:\n');
console.log(`✅ Used: ${report.used.length}`);
console.log(`❌ Unused: ${report.unused.length}`);
console.log(`⚠️  Partially Used: ${report.partiallyUsed.length}\n`);

if (report.unused.length > 0) {
  console.log('❌ Unused Components:\n');
  report.unused.forEach(item => {
    console.log(`  - ${item.component}`);
    console.log(`    Reason: ${item.reason}`);
    if (item.file) {
      console.log(`    File: ${item.file}`);
    }
    console.log();
  });
}

// Exit with error code if unused components found
process.exit(report.unused.length > 0 ? 1 : 0);

