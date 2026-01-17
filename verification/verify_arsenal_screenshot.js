const { chromium } = require('playwright');
const path = require('path');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();

    // 1. Inject localStorage data
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

        localStorage.setItem('tytax_user_profile', JSON.stringify({ name: "Tester" }));
        localStorage.setItem('tytax_logs', '[]');
        // We rely on the app to use PRESETS if masterExercises is not set,
        // OR we can inject masterExercises into localStorage if we want to be sure.
        // But the verification test showed it worked without injecting 'tytax_master_exercises',
        // likely because the app defaults to PRESETS data if empty.
    });

    // 2. Load Page
    const filePath = path.resolve(__dirname, '../index.html');
    await page.goto(`file://${filePath}`);

    // 3. Navigate to Arsenal
    const arsenalTab = page.locator('button', { hasText: 'Arsenal' }).first();
    await arsenalTab.click();

    // Wait for animation/render
    await page.waitForTimeout(500);

    // 4. Take Screenshot of the Arsenal Tab
    await page.screenshot({ path: 'verification/arsenal_tab.png', fullPage: false });

    console.log("Screenshot taken: verification/arsenal_tab.png");
    await browser.close();
})();
