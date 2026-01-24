import os
import json
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch()
    context = browser.new_context()
    page = context.new_page()

    # Pre-populate localStorage to bypass login
    user_profile = {
        "name": "TestUser",
        "bodyweight": 80,
        "goal": "Strength"
    }

    # Navigate to allow localStorage access
    page.goto("http://localhost:8000/index.html")

    page.evaluate(f"""() => {{
        localStorage.setItem('tytax_users_list', '["TestUser"]');
        localStorage.setItem('tytax_user_profile_TestUser', '{json.dumps(user_profile)}');
        localStorage.setItem('tytax_language', 'en');
    }}""")

    page.reload()

    # Click login for TestUser
    # We look for a button that contains the username "TestUser"
    page.get_by_role("button", name="TestUser").click()

    # Wait for App to load (Dashboard)
    page.get_by_text("System Status").wait_for()

    # Navigate to Arsenal using the button in the nav
    # The nav button has "Arsenal" text. But there might be duplicate navs (mobile/desktop).
    # .first should handle it.
    page.get_by_role("button", name="Arsenal").first.click()

    # Wait for Arsenal to load - verify by Header
    page.get_by_role("heading", name="Arsenal Database").wait_for()

    # Verify list is populated (check for an exercise)
    # This proves getImpact didn't crash the list rendering
    page.get_by_text("Smith Flat Bench Press").first.wait_for()

    # Take screenshot
    page.screenshot(path="verification/arsenal_loaded.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
