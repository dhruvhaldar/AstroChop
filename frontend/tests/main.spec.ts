import { test, expect } from '@playwright/test';

test.describe('Next.js Landing Page', () => {
  test('has expected title', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Create Next App/);
  });

  test('has expected main content', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('To get started, edit the page.tsx file.')).toBeVisible();
    await expect(page.getByText('Looking for a starting point or more instructions?')).toBeVisible();
  });

  test('has links to Templates and Learning center', async ({ page }) => {
    await page.goto('/');
    const templatesLink = page.getByRole('link', { name: 'Templates' });
    await expect(templatesLink).toBeVisible();
    await expect(templatesLink).toHaveAttribute('href', /vercel.com\/templates/);

    const learningLink = page.getByRole('link', { name: 'Learning' });
    await expect(learningLink).toBeVisible();
    await expect(learningLink).toHaveAttribute('href', /nextjs.org\/learn/);
  });

  test('has Deploy Now and Documentation links', async ({ page }) => {
    await page.goto('/');
    const deployLink = page.getByRole('link', { name: /Deploy Now/i });
    await expect(deployLink).toBeVisible();
    await expect(deployLink).toHaveAttribute('href', /vercel.com\/new/);

    const docsLink = page.getByRole('link', { name: /Documentation/i });
    await expect(docsLink).toBeVisible();
    await expect(docsLink).toHaveAttribute('href', /nextjs.org\/docs/);
  });
});
