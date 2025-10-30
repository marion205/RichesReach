// API Base Configuration Test
import { API_BASE } from '../src/config/api';

describe('API Base Configuration', () => {
  test('API_BASE should not use port 8001', () => {
    expect(/:8001/.test(API_BASE)).toBe(false);
  });

  test('API_BASE should not use localhost:8001', () => {
    expect(/localhost:8001/.test(API_BASE)).toBe(false);
  });

  test('API_BASE should not use 127.0.0.1:8001', () => {
    expect(/127\.0\.0\.1:8001/.test(API_BASE)).toBe(false);
  });

  test('API_BASE should be a valid URL', () => {
    expect(() => new URL(API_BASE)).not.toThrow();
  });

  test('API_BASE should use HTTP or HTTPS protocol', () => {
    expect(API_BASE).toMatch(/^https?:\/\//);
  });
});
