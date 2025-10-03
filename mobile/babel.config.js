// mobile/babel.config.js
module.exports = function (api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],           // (or 'module:metro-react-native-babel-preset' if you're bare RN)
    plugins: [
      // Do NOT include 'react-native-worklets/plugin'
      'react-native-reanimated/plugin',       // keep LAST
    ],
  };
};
