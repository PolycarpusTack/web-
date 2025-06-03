import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should display login page', async ({ page }) => {
    await page.goto('/login');
    
    // Check for login form elements
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
    await expect(page.getByLabel(/username/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.goto('/login');
    
    // Fill in login form
    await page.getByLabel(/username/i).fill('testuser');
    await page.getByLabel(/password/i).fill('test123!');
    
    // Submit form
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Should redirect to dashboard
    await expect(page).toHaveURL(/\/$/);
    
    // Should show user menu
    await expect(page.getByRole('button', { name: /user menu/i })).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');
    
    // Fill in login form with invalid credentials
    await page.getByLabel(/username/i).fill('invaliduser');
    await page.getByLabel(/password/i).fill('wrongpassword');
    
    // Submit form
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Should show error message
    await expect(page.getByText(/invalid credentials/i)).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    // First login
    await page.goto('/login');
    await page.getByLabel(/username/i).fill('testuser');
    await page.getByLabel(/password/i).fill('test123!');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Wait for redirect
    await expect(page).toHaveURL(/\/$/);
    
    // Open user menu and logout
    await page.getByRole('button', { name: /user menu/i }).click();
    await page.getByRole('menuitem', { name: /logout/i }).click();
    
    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should redirect to login when accessing protected route', async ({ page }) => {
    // Try to access protected route without authentication
    await page.goto('/pipelines');
    
    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });
});