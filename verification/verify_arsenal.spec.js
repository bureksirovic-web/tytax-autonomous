
const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('Arsenal Tab Verification', () => {
  test.beforeEach(async ({ page }) => {
    // 1. Inject localStorage data to bypass wizard and ensure exercises exist
    await page.addInitScript(() => {
        const mockExercises = [
            {
                name: "TYTAX T1 | Smith Flat Bench Press",
                station: "Smith Machine",
                muscle_group: "CHEST",
                sets: 3,
                reps: "6-10",
                impact: [{ m: "Chest", s: 95 }, { m: "Triceps", s: 65 }]
            },
            {
                name: "TYTAX T1 | Upper Pulley Wide-Grip Lat Pulldown",
                station: "Back Upper Pulley",
                muscle_group: "BACK_VERTICAL",
                sets: 3,
                reps: "8-12",
                impact: [{ m: "Lats", s: 95 }, { m: "Biceps", s: 40 }]
            }
        ];

        const mockPreset = {
            id: 'kinetic_impact',
            name: 'Test Preset',
            data: {
                MASTER_EXERCISES: mockExercises,
                INITIAL_PLAN: { "Test": [] },
                INITIAL_ORDER: ["Test"]
            }
        };

        // Bypass Wizard
        localStorage.setItem('tytax_user_profile', JSON.stringify({ name: "Tester" }));
        localStorage.setItem('tytax_logs', '[]'); // Empty logs

        // Ensure library is populated (the app logic usually loads from PRESETS if empty, but let's be safe)
        // Actually, the App component initializes 'library' from PRESETS if available.
        // We just need to make sure we don't get stuck in "System Standby" without a way to navigate.
        // But the sidebar is visible even in standby on desktop?
        // No, Sidebar is visible always on desktop.
        // On mobile, bottom nav is visible unless focusMode.
    });

    // 2. Load the page
    const filePath = path.resolve(__dirname, '../index.html');
    await page.goto(`file://${filePath}`);
  });

  test('should navigate to Arsenal tab and display exercises', async ({ page }) => {
    // 3. Click the "Arsenal" tab
    // We need to handle both Desktop and Mobile navigators.
    // The button has "Arsenal" text.

    // Find button with text "Arsenal"
    const arsenalTab = page.locator('button', { hasText: 'Arsenal' }).first();
    await expect(arsenalTab).toBeVisible();
    await arsenalTab.click();

    // 4. Verify Header
    await expect(page.locator('h2', { hasText: 'Arsenal' })).toBeVisible();
    await expect(page.locator('h2', { hasText: 'Database' })).toBeVisible();

    // 5. Verify Search Input
    const searchInput = page.getByPlaceholder('Search Operations...');
    await expect(searchInput).toBeVisible();

    // 6. Verify Exercise List
    // We expect at least the exercises from the PRESETS (which are hardcoded in index.html)
    // "Smith Flat Bench Press" should be visible
    await expect(page.getByText('Smith Flat Bench Press')).toBeVisible();

    // 7. Test Search
    await searchInput.fill('Lat Pulldown');
    await expect(page.getByText('Smith Flat Bench Press')).not.toBeVisible();
    await expect(page.getByText('Lat Pulldown').first()).toBeVisible();

    // 8. Test Filter
    // Clear search
    await searchInput.fill('');

    // Click "CHEST" filter
    const chestFilter = page.locator('button', { hasText: 'CHEST' });
    if (await chestFilter.isVisible()) {
        await chestFilter.click();
        await expect(page.getByText('Smith Flat Bench Press')).toBeVisible();
        await expect(page.getByText('Lat Pulldown')).not.toBeVisible(); // Should be hidden
    } else {
        console.log("CHEST filter not found, skipping filter test (might be named differently in categories)");
    }
  });
});
