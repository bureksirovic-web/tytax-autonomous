const { test, expect } = require('@playwright/test');

test.describe('System Manual Verification', () => {
  test.beforeEach(async ({ page, context }) => {
    // Inject user profile to bypass wizards
    await context.addInitScript(() => {
      window.localStorage.setItem('tytax_user_profile', JSON.stringify({ name: 'Commander', experience: 'Elite' }));
      window.localStorage.setItem('tytax_logs', '[]');
      window.localStorage.setItem('tytax_session_order', '["Upper A", "Lower A"]');
    });

    await page.goto('file://' + process.cwd() + '/index.html');

    // Wait for hydration
    await page.waitForSelector('#root');
  });

  test('Manual page should not have duplicate content', async ({ page }) => {
    // Navigate to Manual/Features tab
    await page.click('button:has-text("Manual")'); // Sidebar label is 'Manual' on desktop, 'Features' on mobile

    // Check for unique section headers that should only appear once

    // "Trends Intelligence" should appear exactly once in the content area
    const trendsHeader = page.getByRole('heading', { name: 'Trends Intelligence' });
    await expect(trendsHeader).toBeVisible();
    await expect(trendsHeader).toHaveCount(1);

    // "Master Node" header in the manual content
    const masterNodeHeader = page.getByRole('heading', { name: 'Master Node', level: 3 });
    await expect(masterNodeHeader).toBeVisible();

    // "Field Operations" header
    const fieldOpsHeader = page.getByRole('heading', { name: 'Field Operations', level: 3 });
    await expect(fieldOpsHeader).toBeVisible();
  });

  test('Architect Module section should contain detailed steps', async ({ page }) => {
    await page.click('button:has-text("Manual")');

    // Check for the specific text we added
    await expect(page.getByText('Protocol Wizard', { exact: false })).toBeVisible();
    await expect(page.getByText('Program Manager', { exact: false })).toBeVisible();

    // Use a more specific locator for Session Editor to avoid ambiguity with description text
    // The header has "uppercase" class logic or we can just check count > 0
    const sessionEditorTexts = await page.getByText('Session Editor').all();
    expect(sessionEditorTexts.length).toBeGreaterThan(0);

    // Verify one of them is the block header
    const header = page.locator('span.uppercase', { hasText: 'Session Editor' }).first();
    await expect(header).toBeVisible();
  });

  test('No console errors', async ({ page }) => {
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text());
    });

    await page.click('button:has-text("Manual")');
    expect(errors).toEqual([]);
  });
});
