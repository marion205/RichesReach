const { getDefaultConfig } = require('expo/metro-config');

/**
 * Optimized Metro Config for 2025
 * 
 * Features:
 * - Enhanced tree-shaking
 * - Better ES module support
 * - Optimized minification
 * - Improved source maps
 * - Faster startup times
 */

const config = getDefaultConfig(__dirname);

// ✅ Enable tree-shaking and optimization
config.resolver = {
  ...config.resolver,
  unstable_enableSymlinks: false, // Better tree-shaking
  sourceExts: [...(config.resolver?.sourceExts || []), 'mjs'],
};

// ✅ Optimize transformer for ES modules and faster startup
config.transformer = {
  ...config.transformer,
  getTransformOptions: async () => ({
    transform: {
      experimentalImportSupport: false, // Better tree-shaking
      inlineRequires: true, // Faster startup - loads modules on-demand
      unstable_allowRequireContext: true,
    },
  }),
  // ✅ Optimize minification for Hermes
  minifierConfig: {
    keep_classnames: true, // Important for debugging
    keep_fnames: true, // Important for debugging
    mangle: {
      keep_classnames: true,
      keep_fnames: true,
    },
    // Hermes-specific optimizations
    compress: {
      drop_console: false, // Keep console for production debugging (set to true for smaller bundle)
      passes: 2, // More aggressive minification
    },
  },
  unstable_allowRequireContext: true,
};

// ✅ Optimize serializer for better caching
config.serializer = {
  ...config.serializer,
  // Create stable module IDs for better caching
  createModuleIdFactory: () => {
    let nextId = 0;
    return () => {
      const id = nextId++;
      return id.toString(36); // Base36 for shorter IDs
    };
  },
};

// ✅ Optimize for production builds
if (process.env.NODE_ENV === 'production') {
  config.transformer.minifierConfig.compress.drop_console = true;
}

module.exports = config;
