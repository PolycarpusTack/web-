import { test, expect } from '@playwright/test';

// Phase 2 Performance Targets
const PERFORMANCE_TARGETS = {
  pageLoad: 1000, // 1 second
  apiResponse: 200, // 200ms
  timeToInteractive: 2000, // 2 seconds
  lcp: 2500, // 2.5 seconds (Good LCP)
  fid: 100, // 100ms (Good FID)
  cls: 0.1, // 0.1 (Good CLS)
};

test.describe('Performance Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Enable performance metrics collection
    await page.coverage.startJSCoverage();
  });

  test.afterEach(async ({ page }) => {
    await page.coverage.stopJSCoverage();
  });

  test('homepage should load within performance budget', async ({ page }) => {
    const startTime = Date.now();
    
    // Navigate and wait for load
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    // Check page load time
    expect(loadTime).toBeLessThan(PERFORMANCE_TARGETS.pageLoad);
    
    // Measure Core Web Vitals
    const metrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        let lcp = 0;
        let fid = 0;
        let cls = 0;
        
        // Observe LCP
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          lcp = entries[entries.length - 1].startTime;
        }).observe({ type: 'largest-contentful-paint', buffered: true });
        
        // Get FID (First Input Delay) - simplified measurement
        if (performance.getEntriesByType('first-input').length > 0) {
          fid = performance.getEntriesByType('first-input')[0].processingStart - 
                performance.getEntriesByType('first-input')[0].startTime;
        }
        
        // Calculate CLS
        let clsValue = 0;
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          }
          cls = clsValue;
        }).observe({ type: 'layout-shift', buffered: true });
        
        // Wait a bit for metrics to be collected
        setTimeout(() => {
          resolve({ lcp, fid, cls });
        }, 1000);
      });
    });
    
    // Assert Core Web Vitals meet targets
    expect(metrics.lcp).toBeLessThan(PERFORMANCE_TARGETS.lcp);
    if (metrics.fid > 0) {
      expect(metrics.fid).toBeLessThan(PERFORMANCE_TARGETS.fid);
    }
    expect(metrics.cls).toBeLessThan(PERFORMANCE_TARGETS.cls);
  });

  test('API endpoints should respond within 200ms', async ({ page }) => {
    await page.goto('/');
    
    // Monitor API calls
    const apiCalls: number[] = [];
    
    page.on('response', async (response) => {
      if (response.url().includes('/api/')) {
        const timing = response.timing();
        if (timing) {
          apiCalls.push(timing.responseEnd - timing.requestStart);
        }
      }
    });
    
    // Trigger some API calls
    await page.goto('/models');
    await page.waitForLoadState('networkidle');
    
    // Check API response times
    for (const responseTime of apiCalls) {
      expect(responseTime).toBeLessThan(PERFORMANCE_TARGETS.apiResponse);
    }
  });

  test('chat interface should be interactive quickly', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('/chat');
    
    // Wait for chat input to be interactive
    await page.locator('textarea[placeholder*="Type your message"]').waitFor({ state: 'visible' });
    
    const timeToInteractive = Date.now() - startTime;
    expect(timeToInteractive).toBeLessThan(PERFORMANCE_TARGETS.timeToInteractive);
    
    // Verify chat is actually interactive
    await page.fill('textarea[placeholder*="Type your message"]', 'Test message');
    expect(await page.locator('textarea[placeholder*="Type your message"]').inputValue()).toBe('Test message');
  });

  test('pipeline builder should handle complex operations efficiently', async ({ page }) => {
    await page.goto('/pipelines/builder');
    
    const startTime = Date.now();
    
    // Add multiple pipeline steps
    for (let i = 0; i < 5; i++) {
      await page.click('button:has-text("Add Step")');
      await page.waitForTimeout(100); // Small delay between operations
    }
    
    const operationTime = Date.now() - startTime;
    
    // Should handle multiple operations without significant lag
    expect(operationTime).toBeLessThan(2000); // 2 seconds for 5 operations
  });

  test('memory usage should remain stable', async ({ page }) => {
    await page.goto('/');
    
    // Get initial memory usage
    const initialMemory = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory.usedJSHeapSize;
      }
      return 0;
    });
    
    // Navigate through the app
    await page.goto('/models');
    await page.goto('/chat');
    await page.goto('/pipelines');
    await page.goto('/');
    
    // Get final memory usage
    const finalMemory = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory.usedJSHeapSize;
      }
      return 0;
    });
    
    // Memory increase should be reasonable (less than 50MB)
    const memoryIncrease = (finalMemory - initialMemory) / 1024 / 1024;
    expect(memoryIncrease).toBeLessThan(50);
  });

  test('should track render performance', async ({ page }) => {
    await page.goto('/models');
    
    // Measure React render performance
    const renderMetrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const renderTimes = entries
            .filter(entry => entry.name.includes('render'))
            .map(entry => entry.duration);
          resolve(renderTimes);
        });
        observer.observe({ entryTypes: ['measure'] });
        
        // Wait for renders to complete
        setTimeout(() => resolve([]), 2000);
      });
    });
    
    // Check if any renders are taking too long
    if (Array.isArray(renderMetrics)) {
      for (const renderTime of renderMetrics) {
        expect(renderTime).toBeLessThan(16); // 60fps = 16ms per frame
      }
    }
  });
});

test.describe('Performance Regression Tests', () => {
  test('should not regress on critical user paths', async ({ page }) => {
    const criticalPaths = [
      { path: '/', name: 'Homepage' },
      { path: '/models', name: 'Models Page' },
      { path: '/chat', name: 'Chat Page' },
      { path: '/pipelines', name: 'Pipelines Page' },
    ];
    
    const results: Record<string, number> = {};
    
    for (const { path, name } of criticalPaths) {
      const startTime = Date.now();
      await page.goto(path);
      await page.waitForLoadState('networkidle');
      results[name] = Date.now() - startTime;
    }
    
    // Log results for tracking
    console.log('Performance Results:', results);
    
    // Assert all paths load within budget
    for (const [name, time] of Object.entries(results)) {
      expect(time).toBeLessThan(PERFORMANCE_TARGETS.pageLoad);
    }
  });
});