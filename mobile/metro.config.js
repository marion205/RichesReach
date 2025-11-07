const { getDefaultConfig } = require('@expo/metro-config');

const config = getDefaultConfig(__dirname);

config.resolver.sourceExts = [...config.resolver.sourceExts, 'cjs'];

config.resolver.blockList = [/ios\/build\/.*/, /android\/build\/.*/];

module.exports = config;
