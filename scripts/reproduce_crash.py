
import asyncio
from playwright.async_api import async_playwright
import os

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        # Inject localStorage to set language to 'hr' AND bypass Wizard
        await context.add_init_script("""
            localStorage.setItem('tytax_language', 'hr');
            if (!localStorage.getItem('tytax_logs')) {
                localStorage.setItem('tytax_logs', '[]');
            }
            // Bypass Welcome Wizard by setting profile
            localStorage.setItem('tytax_user_profile', JSON.stringify({
                name: 'Test Commander',
                units: 'KG',
                bodyweight: '80'
            }));
            // Bypass System Standby by setting session order
            localStorage.setItem('tytax_session_order', JSON.stringify(['Upper A', 'Lower A']));
            localStorage.setItem('tytax_training_plan', JSON.stringify({'Upper A': [], 'Lower A': []}));
        """)

        page = await context.new_page()

        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"PAGE ERROR: {exc}"))

        print("Loading page...")
        # Point to the index.html one level up from this script's directory
        app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../index.html"))
        await page.goto(f"file://{app_path}")
        await page.wait_for_timeout(2000)

        # Check for Settings button (Postavke)
        settings_btn = page.locator("button", has_text="Postavke").first
        if await settings_btn.is_visible():
            print("SUCCESS: Settings button (Postavke) is visible.")
        else:
            print("FAILURE: Settings button not found.")

        # Navigate to Trends (Trendovi)
        print("Navigating to Trends...")
        await page.click("button:has-text('Trendovi')")
        await page.wait_for_timeout(2000)

        # Check if Trends loaded (look for unique text 'Tjedni Volumen')
        if await page.locator("text=Tjedni Volumen").first.is_visible():
             print("SUCCESS: Trends tab loaded.")
        else:
             print("FAILURE: Trends tab did not load properly.")

        # Navigate to Builder (Graditelj)
        print("Navigating to Builder...")
        await page.click("button:has-text('Graditelj')")
        await page.wait_for_timeout(2000)

        # Check if Builder loaded (look for 'Učestalost' from 'Učestalost Treninga')
        if await page.locator("text=Učestalost").first.is_visible():
             print("SUCCESS: Builder tab loaded.")
        else:
             print("FAILURE: Builder tab did not load properly.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
