/**
 * Test Infrastructure Verification
 * Validates that the testing setup is working correctly
 */

import { describe, it, expect, vi } from 'vitest';

describe('Test Infrastructure', () => {
  describe('Basic Vitest Setup', () => {
    it('should run basic assertions', () => {
      expect(1 + 1).toBe(2);
      expect('hello').toBe('hello');
      expect([1, 2, 3]).toHaveLength(3);
    });

    it('should handle async operations', async () => {
      const asyncFunction = async () => {
        return Promise.resolve('success');
      };
      
      const result = await asyncFunction();
      expect(result).toBe('success');
    });

    it('should support mocking with vi', () => {
      const mockFn = vi.fn();
      mockFn('test');
      
      expect(mockFn).toHaveBeenCalledWith('test');
      expect(mockFn).toHaveBeenCalledTimes(1);
    });
  });

  describe('DOM Environment', () => {
    it('should have access to DOM APIs', () => {
      const div = document.createElement('div');
      div.textContent = 'Test content';
      document.body.appendChild(div);
      
      expect(document.body.textContent).toContain('Test content');
      
      // Cleanup
      document.body.removeChild(div);
    });

    it('should have window object available', () => {
      expect(window).toBeDefined();
      expect(window.location).toBeDefined();
      expect(window.localStorage).toBeDefined();
    });

    it('should have mocked APIs available', () => {
      expect(window.matchMedia).toBeDefined();
      expect(global.ResizeObserver).toBeDefined();
      expect(global.IntersectionObserver).toBeDefined();
    });
  });

  describe('Module Resolution', () => {
    it('should resolve TypeScript modules', () => {
      // This test itself proves TS module resolution is working
      expect(typeof describe).toBe('function');
      expect(typeof it).toBe('function');
      expect(typeof expect).toBe('function');
    });

    it('should handle ES modules correctly', () => {
      // Test that ES module imports work
      expect(vi).toBeDefined();
      expect(vi.fn).toBeDefined();
      expect(vi.mock).toBeDefined();
    });
  });

  describe('Error Handling', () => {
    it('should catch and report errors properly', () => {
      expect(() => {
        throw new Error('Test error');
      }).toThrow('Test error');
    });

    it('should handle promise rejections', async () => {
      const rejectedPromise = Promise.reject(new Error('Async error'));
      
      await expect(rejectedPromise).rejects.toThrow('Async error');
    });
  });

  describe('Performance', () => {
    it('should complete tests quickly', () => {
      const start = performance.now();
      
      // Simulate some work
      for (let i = 0; i < 1000; i++) {
        Math.random();
      }
      
      const end = performance.now();
      const duration = end - start;
      
      // Should complete in reasonable time (less than 100ms)
      expect(duration).toBeLessThan(100);
    });
  });
});