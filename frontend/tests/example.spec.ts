import { test, expect } from '@playwright/test';

test('has expected content', async ({ page }) => {
  await page.goto('/');

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/Create Next App/);

  // Expect to find a specific text from the template
  await expect(page.getByText('To get started, edit the page.tsx file.')).toBeVisible();
});
