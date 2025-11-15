/**
 * Manual mock for PixelRatio to ensure it loads before StyleSheet
 * This file is automatically used by Jest when react-native/Libraries/Utilities/PixelRatio is imported
 */

module.exports = {
  get: jest.fn(() => 2),
  getFontScale: jest.fn(() => 1),
  isFontScaleAtLeast: jest.fn(() => true),
  roundToNearestPixel: jest.fn((size) => Math.round(size * 2) / 2),
  getPixelSizeForLayoutSize: jest.fn((size) => size * 2),
  startDetecting: jest.fn(),
};

