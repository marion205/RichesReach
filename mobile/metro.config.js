const { getDefaultConfig } = require('expo/metro-config');

// Minimal, Node-loadable CommonJS config
const config = getDefaultConfig(__dirname);
module.exports = config;
