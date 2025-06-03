import { Page } from '@playwright/test';

export async function login(page: Page, username: string = 'testuser', password: string = 'test123!') {
  await page.goto('/login');
  await page.getByLabel(/username/i).fill(username);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole('button', { name: /sign in/i }).click();
  await page.waitForURL(/\/$/);
}

export async function logout(page: Page) {
  await page.getByRole('button', { name: /user menu/i }).click();
  await page.getByRole('menuitem', { name: /logout/i }).click();
  await page.waitForURL(/\/login/);
}

export async function ensureLoggedIn(page: Page) {
  // Check if already logged in
  const isLoggedIn = await page.getByRole('button', { name: /user menu/i }).isVisible().catch(() => false);
  
  if (!isLoggedIn) {
    await login(page);
  }
}