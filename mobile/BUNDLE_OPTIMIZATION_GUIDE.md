# Bundle Size Optimization Guide

## Overview

This guide helps you analyze and optimize the React Native bundle size for RichesReach.

## Quick Start

### Analyze Bundle Size

```bash
# Analyze iOS bundle
npm run bundle:analyze:ios

# Analyze Android bundle
npm run bundle:analyze:android

# Analyze current platform
npm run bundle:analyze
```

### View Results

After running the analysis, open the generated HTML report:
- iOS: `bundle-analysis/ios-report.html`
- Android: `bundle-analysis/android-report.html`

## Bundle Size Targets

| Platform | Target | Warning | Critical |
|----------|--------|---------|----------|
| iOS | < 2 MB | 2-3 MB | > 3 MB |
| Android | < 2 MB | 2-3 MB | > 3 MB |

## Optimization Strategies

### 1. Code Splitting

Use dynamic imports for heavy screens:

```typescript
// ❌ Bad: Eager loading
import HeavyScreen from './screens/HeavyScreen';

// ✅ Good: Lazy loading
const HeavyScreen = React.lazy(() => import('./screens/HeavyScreen'));
```

### 2. Remove Unused Dependencies

```bash
# Find unused dependencies
npx depcheck

# Remove unused packages
npm uninstall <package-name>
```

### 3. Optimize Images

- Use WebP format when possible
- Compress images before adding to assets
- Use `react-native-fast-image` for better caching
- Consider using CDN for large images

### 4. Tree Shaking

Ensure your bundler can tree-shake unused code:

```typescript
// ❌ Bad: Imports entire library
import _ from 'lodash';
const result = _.map(array, fn);

// ✅ Good: Import only what you need
import map from 'lodash/map';
const result = map(array, fn);
```

### 5. Enable Hermes

Hermes provides better compression and performance:

```json
// android/app/build.gradle
project.ext.react = [
    enableHermes: true
]
```

### 6. Analyze Large Dependencies

Check which dependencies are taking up space:

```bash
# View dependency sizes
npx source-map-explorer bundle-analysis/ios-bundle.js --json | jq '.results | sort_by(.size) | reverse | .[0:10]'
```

## Common Large Dependencies

| Package | Size | Alternative |
|----------|------|-----------|
| `lodash` | ~70 KB | `lodash-es` (tree-shakeable) |
| `moment` | ~70 KB | `date-fns` or `dayjs` |
| `react-native-vector-icons` | ~500 KB | Use only needed icon sets |
| `@apollo/client` | ~200 KB | Already optimized |

## Monitoring

### Pre-commit Checks

Add bundle size checks to CI/CD:

```bash
# In CI pipeline
npm run bundle:analyze:ios
npm run bundle:analyze:android

# Fail if bundle exceeds threshold
node scripts/check-bundle-size.js
```

### Regular Audits

Run bundle analysis:
- Before each release
- After adding large dependencies
- Monthly for ongoing optimization

## Tools

- **react-native-bundle-visualizer**: Visual bundle analysis
- **source-map-explorer**: Detailed size breakdown
- **depcheck**: Find unused dependencies
- **bundlephobia**: Check package sizes before installing

## Best Practices

1. **Import only what you need**
   ```typescript
   // ✅ Good
   import { map } from 'lodash-es';
   
   // ❌ Bad
   import _ from 'lodash';
   ```

2. **Use lazy loading for routes**
   ```typescript
   const Screen = React.lazy(() => import('./Screen'));
   ```

3. **Split vendor bundles**
   - Separate app code from vendor code
   - Use code splitting for large features

4. **Monitor bundle size over time**
   - Track size in CI/CD
   - Set alerts for size increases

## Troubleshooting

### Bundle size increased unexpectedly

1. Check recent dependency additions
2. Look for duplicate dependencies
3. Verify tree-shaking is working
4. Check for large assets added recently

### Analysis script fails

1. Ensure bundle is generated first
2. Check that source maps are enabled
3. Verify all dependencies are installed

## Resources

- [React Native Performance](https://reactnative.dev/docs/performance)
- [Metro Bundler Configuration](https://reactnative.dev/docs/metro)
- [Hermes Engine](https://hermesengine.dev/)

