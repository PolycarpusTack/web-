import { test, expect } from '@playwright/test';

test.describe('Chat Interface', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.getByLabel(/username/i).fill('testuser');
    await page.getByLabel(/password/i).fill('test123!');
    await page.getByRole('button', { name: /sign in/i }).click();
    await expect(page).toHaveURL(/\/$/);
  });

  test('should create new conversation', async ({ page }) => {
    await page.goto('/chat');
    
    // Click new conversation button
    await page.getByRole('button', { name: /new conversation/i }).click();
    
    // Fill in conversation details
    await page.getByLabel(/title/i).fill('Test Conversation');
    await page.getByLabel(/model/i).selectOption('llama3.2:latest');
    
    // Create conversation
    await page.getByRole('button', { name: /create/i }).click();
    
    // Should show new conversation
    await expect(page.getByText('Test Conversation')).toBeVisible();
  });

  test('should send and receive messages', async ({ page }) => {
    await page.goto('/chat');
    
    // Select or create a conversation
    const conversationExists = await page.getByText('Welcome Conversation').isVisible().catch(() => false);
    
    if (!conversationExists) {
      await page.getByRole('button', { name: /new conversation/i }).click();
      await page.getByLabel(/title/i).fill('Test Chat');
      await page.getByRole('button', { name: /create/i }).click();
    }
    
    // Type a message
    const messageInput = page.getByPlaceholder(/type a message/i);
    await messageInput.fill('Hello, how are you?');
    
    // Send message
    await page.getByRole('button', { name: /send/i }).click();
    
    // Should show user message
    await expect(page.getByText('Hello, how are you?')).toBeVisible();
    
    // Should show AI response (streaming)
    await expect(page.locator('[data-testid="ai-message"]')).toBeVisible({ timeout: 10000 });
  });

  test('should show streaming indicator', async ({ page }) => {
    await page.goto('/chat');
    
    // Send a message
    const messageInput = page.getByPlaceholder(/type a message/i);
    await messageInput.fill('Tell me a story');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Should show streaming indicator
    await expect(page.getByTestId('streaming-indicator')).toBeVisible();
    
    // Should hide after completion
    await expect(page.getByTestId('streaming-indicator')).not.toBeVisible({ timeout: 15000 });
  });

  test('should handle file attachments', async ({ page }) => {
    await page.goto('/chat');
    
    // Click file upload button
    await page.getByRole('button', { name: /attach file/i }).click();
    
    // Upload a file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('This is a test file content')
    });
    
    // Should show file preview
    await expect(page.getByText('test.txt')).toBeVisible();
    
    // Send message with attachment
    await page.getByPlaceholder(/type a message/i).fill('Analyze this file');
    await page.getByRole('button', { name: /send/i }).click();
    
    // Should show message with attachment
    await expect(page.getByText('Analyze this file')).toBeVisible();
    await expect(page.locator('[data-testid="attachment-preview"]')).toBeVisible();
  });

  test('should export conversation', async ({ page }) => {
    await page.goto('/chat');
    
    // Open conversation menu
    await page.getByRole('button', { name: /conversation menu/i }).click();
    
    // Click export
    await page.getByRole('menuitem', { name: /export/i }).click();
    
    // Should show export dialog
    await expect(page.getByRole('dialog', { name: /export conversation/i })).toBeVisible();
    
    // Select export format
    await page.getByRole('radio', { name: /markdown/i }).click();
    
    // Export
    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: /export/i }).click();
    const download = await downloadPromise;
    
    // Verify download
    expect(download.suggestedFilename()).toContain('.md');
  });
});