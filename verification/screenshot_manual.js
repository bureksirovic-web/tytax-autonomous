
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // Inject user profile to bypass wizards and ensure we see the full interface
  await page.addInitScript(() => {
    window.localStorage.setItem('tytax_user_profile', JSON.stringify({ name: 'Commander', experience: 'Elite' }));
    window.localStorage.setItem('tytax_logs', '[]');
    window.localStorage.setItem('tytax_session_order', '["Upper A", "Lower A"]');
  });

  const filePath = 'file://' + path.join(process.cwd(), 'index.html');
  await page.goto(filePath);

  // Navigate to Manual/Features tab
  await page.click('button:has-text("Manual")'); // Sidebar label is 'Manual' on desktop

  // Wait for content
  await page.waitForTimeout(500);

  // Take full page screenshot of the Manual section
  await page.screenshot({ path: 'verification/manual_screenshot.png', fullPage: true });

  await browser.close();
})();
