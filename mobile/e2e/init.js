const { detox, device, element, by, waitFor, expect } = require('detox');

beforeAll(async () => {
  await detox.init();
});

afterAll(async () => {
  await detox.cleanup();
});

beforeEach(async () => {
  await device.reloadReactNative();
});
