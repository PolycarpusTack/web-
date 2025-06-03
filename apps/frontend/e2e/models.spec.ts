import { test, expect } from '@playwright/test';

test.describe('Model Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.getByLabel(/username/i).fill('testuser');
    await page.getByLabel(/password/i).fill('test123!');
    await page.getByRole('button', { name: /sign in/i }).click();
    await expect(page).toHaveURL(/\/$/);
  });

  test('should display models page', async ({ page }) => {
    await page.goto('/models');
    
    // Check for page elements
    await expect(page.getByRole('heading', { name: /models/i })).toBeVisible();
    await expect(page.getByPlaceholder(/search models/i)).toBeVisible();
    
    // Should show at least one model
    await expect(page.locator('[data-testid="model-card"]')).toHaveCount(3); // Based on seed data
  });

  test('should search for models', async ({ page }) => {
    await page.goto('/models');
    
    // Search for specific model
    await page.getByPlaceholder(/search models/i).fill('llama');
    
    // Should filter results
    const modelCards = page.locator('[data-testid="model-card"]');
    await expect(modelCards).toHaveCount(2); // Llama 3.2 and Code Llama
  });

  test('should view model details', async ({ page }) => {
    await page.goto('/models');
    
    // Click on first model card
    await page.locator('[data-testid="model-card"]').first().click();
    
    // Should show model details
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText(/context window/i)).toBeVisible();
    await expect(page.getByText(/max output tokens/i)).toBeVisible();
  });

  test('should start and stop model', async ({ page }) => {
    await page.goto('/models');
    
    // Find inactive model and start it
    const inactiveModel = page.locator('[data-testid="model-card"]').filter({
      has: page.getByText(/inactive/i)
    }).first();
    
    await inactiveModel.getByRole('button', { name: /start/i }).click();
    
    // Should show loading state
    await expect(inactiveModel.getByText(/starting/i)).toBeVisible();
    
    // Wait for model to start (mocked in tests)
    await expect(inactiveModel.getByText(/active/i)).toBeVisible({ timeout: 10000 });
    
    // Stop the model
    await inactiveModel.getByRole('button', { name: /stop/i }).click();
    await expect(inactiveModel.getByText(/inactive/i)).toBeVisible({ timeout: 10000 });
  });

  test('should filter models by provider', async ({ page }) => {
    await page.goto('/models');
    
    // Open filter dropdown
    await page.getByRole('button', { name: /filter/i }).click();
    
    // Select Ollama provider
    await page.getByRole('checkbox', { name: /ollama/i }).click();
    
    // Should show only Ollama models
    const modelCards = page.locator('[data-testid="model-card"]');
    const count = await modelCards.count();
    
    for (let i = 0; i < count; i++) {
      await expect(modelCards.nth(i)).toContainText('ollama');
    }
  });
});