import { test, expect, formatViolations } from './axe-test';

test.describe('Accessibility Tests', () => {
  test('login page should have no accessibility violations', async ({ page, makeAxeBuilder }) => {
    await page.goto('/login');
    
    const accessibilityScanResults = await makeAxeBuilder().analyze();
    
    if (accessibilityScanResults.violations.length > 0) {
      console.error('Accessibility violations found:');
      console.error(formatViolations(accessibilityScanResults.violations));
    }
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('home page should have no accessibility violations', async ({ page, makeAxeBuilder }) => {
    // Login first
    await page.goto('/login');
    await page.getByLabel(/username/i).fill('testuser');
    await page.getByLabel(/password/i).fill('test123!');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL(/\/$/);
    
    const accessibilityScanResults = await makeAxeBuilder().analyze();
    
    if (accessibilityScanResults.violations.length > 0) {
      console.error('Accessibility violations found:');
      console.error(formatViolations(accessibilityScanResults.violations));
    }
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('models page should have no accessibility violations', async ({ page, makeAxeBuilder }) => {
    // Login and navigate
    await page.goto('/login');
    await page.getByLabel(/username/i).fill('testuser');
    await page.getByLabel(/password/i).fill('test123!');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL(/\/$/);
    
    await page.goto('/models');
    await page.waitForLoadState('networkidle');
    
    const accessibilityScanResults = await makeAxeBuilder().analyze();
    
    if (accessibilityScanResults.violations.length > 0) {
      console.error('Accessibility violations found:');
      console.error(formatViolations(accessibilityScanResults.violations));
    }
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('chat page should have no accessibility violations', async ({ page, makeAxeBuilder }) => {
    // Login and navigate
    await page.goto('/login');
    await page.getByLabel(/username/i).fill('testuser');
    await page.getByLabel(/password/i).fill('test123!');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL(/\/$/);
    
    await page.goto('/chat');
    await page.waitForLoadState('networkidle');
    
    const accessibilityScanResults = await makeAxeBuilder().analyze();
    
    if (accessibilityScanResults.violations.length > 0) {
      console.error('Accessibility violations found:');
      console.error(formatViolations(accessibilityScanResults.violations));
    }
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('pipelines page should have no accessibility violations', async ({ page, makeAxeBuilder }) => {
    // Login and navigate
    await page.goto('/login');
    await page.getByLabel(/username/i).fill('testuser');
    await page.getByLabel(/password/i).fill('test123!');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL(/\/$/);
    
    await page.goto('/pipelines');
    await page.waitForLoadState('networkidle');
    
    const accessibilityScanResults = await makeAxeBuilder().analyze();
    
    if (accessibilityScanResults.violations.length > 0) {
      console.error('Accessibility violations found:');
      console.error(formatViolations(accessibilityScanResults.violations));
    }
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('keyboard navigation should work throughout the app', async ({ page }) => {
    await page.goto('/login');
    
    // Tab through login form
    await page.keyboard.press('Tab'); // Focus username
    await expect(page.getByLabel(/username/i)).toBeFocused();
    
    await page.keyboard.press('Tab'); // Focus password
    await expect(page.getByLabel(/password/i)).toBeFocused();
    
    await page.keyboard.press('Tab'); // Focus sign in button
    await expect(page.getByRole('button', { name: /sign in/i })).toBeFocused();
    
    // Login using keyboard
    await page.getByLabel(/username/i).fill('testuser');
    await page.getByLabel(/password/i).fill('test123!');
    await page.keyboard.press('Enter');
    
    await page.waitForURL(/\/$/);
    
    // Test main navigation with keyboard
    await page.keyboard.press('Tab'); // Should focus first nav item
    const navLinks = page.getByRole('link');
    const firstNavLink = navLinks.first();
    await expect(firstNavLink).toBeFocused();
  });

  test('screen reader landmarks should be present', async ({ page }) => {
    await page.goto('/login');
    
    // Check for main landmark
    await expect(page.getByRole('main')).toBeVisible();
    
    // Login to see more landmarks
    await page.getByLabel(/username/i).fill('testuser');
    await page.getByLabel(/password/i).fill('test123!');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL(/\/$/);
    
    // Check for navigation landmark
    await expect(page.getByRole('navigation')).toBeVisible();
    
    // Check for proper heading hierarchy
    const h1 = await page.getByRole('heading', { level: 1 }).count();
    expect(h1).toBeGreaterThan(0);
  });

  test('form labels should be properly associated', async ({ page }) => {
    await page.goto('/login');
    
    // Check username input has label
    const usernameInput = page.getByLabel(/username/i);
    await expect(usernameInput).toBeVisible();
    
    // Check password input has label
    const passwordInput = page.getByLabel(/password/i);
    await expect(passwordInput).toBeVisible();
    
    // Check that labels are properly associated (clicking label focuses input)
    await page.getByText(/username/i).click();
    await expect(usernameInput).toBeFocused();
  });

  test('color contrast should meet WCAG standards', async ({ page, makeAxeBuilder }) => {
    await page.goto('/login');
    
    // Run axe specifically for color contrast
    const accessibilityScanResults = await makeAxeBuilder()
      .withTags(['wcag2aa'])
      .include(['color-contrast'])
      .analyze();
    
    if (accessibilityScanResults.violations.length > 0) {
      console.error('Color contrast violations found:');
      console.error(formatViolations(accessibilityScanResults.violations));
    }
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('images should have alt text', async ({ page }) => {
    await page.goto('/login');
    
    // Find all images
    const images = page.locator('img');
    const imageCount = await images.count();
    
    if (imageCount > 0) {
      // Check each image has alt text
      for (let i = 0; i < imageCount; i++) {
        const img = images.nth(i);
        const altText = await img.getAttribute('alt');
        expect(altText).toBeTruthy();
      }
    }
  });

  test('focus indicators should be visible', async ({ page }) => {
    await page.goto('/login');
    
    // Tab to username input
    await page.keyboard.press('Tab');
    
    // Check if focus ring is visible (this is a basic check)
    const usernameInput = page.getByLabel(/username/i);
    const outline = await usernameInput.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        outlineStyle: styles.outlineStyle,
        outlineWidth: styles.outlineWidth,
        outlineColor: styles.outlineColor
      };
    });
    
    // Should have some visible outline when focused
    expect(outline.outlineStyle).not.toBe('none');
  });
});