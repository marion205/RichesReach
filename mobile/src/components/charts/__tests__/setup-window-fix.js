// Fix for React Native Jest window redefinition issue
// This needs to run before React Native's jest/setup.js

// Mock window before React Native tries to redefine it
if (typeof global !== 'undefined' && !global.window) {
  global.window = global.window || {};
  Object.defineProperty(global, 'window', {
    value: global.window,
    writable: true,
    configurable: false, // Prevent redefinition
  });
}

// Also prevent Object.defineProperties from redefining window
const originalDefineProperty = Object.defineProperty;
Object.defineProperty = function(obj, prop, descriptor) {
  if (obj === global && prop === 'window') {
    return global; // Skip redefinition
  }
  return originalDefineProperty.call(this, obj, prop, descriptor);
};

