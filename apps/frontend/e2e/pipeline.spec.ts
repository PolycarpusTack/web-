import { test, expect } from '@playwright/test';

test.describe('Pipeline Builder', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.getByLabel(/username/i).fill('testuser');
    await page.getByLabel(/password/i).fill('test123!');
    await page.getByRole('button', { name: /sign in/i }).click();
    await expect(page).toHaveURL(/\/$/);
  });

  test('should display pipeline builder', async ({ page }) => {
    await page.goto('/pipelines/new');
    
    // Check for builder elements
    await expect(page.getByRole('heading', { name: /pipeline builder/i })).toBeVisible();
    await expect(page.locator('.react-flow')).toBeVisible();
    await expect(page.getByText(/drag nodes/i)).toBeVisible();
  });

  test('should drag and drop nodes', async ({ page }) => {
    await page.goto('/pipelines/new');
    
    // Drag LLM node to canvas
    const llmNode = page.getByTestId('node-llm');
    const canvas = page.locator('.react-flow__viewport');
    
    await llmNode.dragTo(canvas, {
      targetPosition: { x: 200, y: 200 }
    });
    
    // Should create node on canvas
    await expect(page.locator('.react-flow__node')).toHaveCount(1);
  });

  test('should connect nodes', async ({ page }) => {
    await page.goto('/pipelines/new');
    
    // Add two nodes
    const llmNode = page.getByTestId('node-llm');
    const transformNode = page.getByTestId('node-transform');
    const canvas = page.locator('.react-flow__viewport');
    
    await llmNode.dragTo(canvas, {
      targetPosition: { x: 200, y: 200 }
    });
    
    await transformNode.dragTo(canvas, {
      targetPosition: { x: 400, y: 200 }
    });
    
    // Connect nodes
    const sourceHandle = page.locator('.react-flow__node').first().locator('.source');
    const targetHandle = page.locator('.react-flow__node').last().locator('.target');
    
    await sourceHandle.dragTo(targetHandle);
    
    // Should create edge
    await expect(page.locator('.react-flow__edge')).toHaveCount(1);
  });

  test('should configure node settings', async ({ page }) => {
    await page.goto('/pipelines/new');
    
    // Add LLM node
    const llmNode = page.getByTestId('node-llm');
    const canvas = page.locator('.react-flow__viewport');
    
    await llmNode.dragTo(canvas, {
      targetPosition: { x: 200, y: 200 }
    });
    
    // Click on node to open settings
    await page.locator('.react-flow__node').first().click();
    
    // Should show configuration panel
    await expect(page.getByRole('heading', { name: /node configuration/i })).toBeVisible();
    
    // Configure node
    await page.getByLabel(/model/i).selectOption('llama3.2:latest');
    await page.getByLabel(/temperature/i).fill('0.7');
    await page.getByLabel(/prompt/i).fill('Analyze the following text: {{input}}');
    
    // Save configuration
    await page.getByRole('button', { name: /save/i }).click();
  });

  test('should save and load pipeline', async ({ page }) => {
    await page.goto('/pipelines/new');
    
    // Create simple pipeline
    const llmNode = page.getByTestId('node-llm');
    const canvas = page.locator('.react-flow__viewport');
    
    await llmNode.dragTo(canvas, {
      targetPosition: { x: 200, y: 200 }
    });
    
    // Name the pipeline
    await page.getByLabel(/pipeline name/i).fill('Test Pipeline');
    
    // Save pipeline
    await page.getByRole('button', { name: /save pipeline/i }).click();
    
    // Should show success message
    await expect(page.getByText(/pipeline saved/i)).toBeVisible();
    
    // Navigate to pipelines list
    await page.goto('/pipelines');
    
    // Should show saved pipeline
    await expect(page.getByText('Test Pipeline')).toBeVisible();
  });

  test('should execute pipeline', async ({ page }) => {
    await page.goto('/pipelines');
    
    // Open existing pipeline
    await page.getByText('Code Review Pipeline').click();
    
    // Click execute button
    await page.getByRole('button', { name: /execute/i }).click();
    
    // Fill in input
    await page.getByLabel(/input/i).fill('function add(a, b) { return a + b; }');
    
    // Run pipeline
    await page.getByRole('button', { name: /run/i }).click();
    
    // Should show execution progress
    await expect(page.getByText(/executing/i)).toBeVisible();
    
    // Should show results
    await expect(page.getByTestId('execution-results')).toBeVisible({ timeout: 15000 });
  });

  test('should use pipeline templates', async ({ page }) => {
    await page.goto('/pipelines/new');
    
    // Click templates button
    await page.getByRole('button', { name: /templates/i }).click();
    
    // Select a template
    await page.getByText('Content Generation Pipeline').click();
    
    // Should load template
    await expect(page.locator('.react-flow__node')).toHaveCount(2); // Template has 2 nodes
    await expect(page.getByLabel(/pipeline name/i)).toHaveValue('Content Generation Pipeline');
  });
});