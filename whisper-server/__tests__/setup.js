// Test setup for Whisper server
const path = require('path');

// Set test environment variables
process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test-secret-key';
process.env.WHISPER_MODEL = 'ggml-tiny.en-q5_0.bin';
process.env.WHISPER_PATH = './whisper.cpp';
process.env.MONGODB_URI = 'mongodb://localhost:27017/richesreach_whisper_test';
process.env.PORT = '3001';

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
};

// Global test timeout
jest.setTimeout(10000);
