
const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('App Startup & Crash Check', () => {
    test.beforeEach(async ({ page, context }) => {
        // Mock localStorage if needed, but we start clean to check default behavior
        await context.addInitScript(() => {
            // Ensure TRANSLATIONS is available (it loads via script tag, but just in case)
        });
    });

    test('should load without critical system failure on clean state', async ({ page }) => {
        const fileUrl = 'file://' + path.resolve(__dirname, '../index.html');

        await page.goto(fileUrl);

        // Allow React to mount
        await page.waitForTimeout(1000);

        // Check for Error Boundary text in Croatian or English
        const errorTextHr = await page.getByText('GREŠKA SUSTAVA').count();
        const errorTextEn = await page.getByText('SYSTEM FAILURE').count();

        expect(errorTextHr).toBe(0);
        expect(errorTextEn).toBe(0);
    });

    test('should verify default language is English', async ({ page }) => {
        const fileUrl = 'file://' + path.resolve(__dirname, '../index.html');
        await page.goto(fileUrl);
        await page.waitForTimeout(1000);

        // The Welcome Wizard should be visible on clean start.
        // Title: "Welcome, Commander" (English) vs "Dobrodošao, Zapovjedniče" (Croatian)

        const welcomeTitle = page.getByRole('heading', { name: /Welcome/i });
        const croatianTitle = page.getByRole('heading', { name: /Dobrodošao/i });

        await expect(welcomeTitle).toBeVisible();
        await expect(croatianTitle).toBeHidden();
    });
});
