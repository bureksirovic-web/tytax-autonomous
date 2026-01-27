from playwright.sync_api import sync_playwright
import time
import os

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()

    # Pre-populate LocalStorage to simulate an existing user
    # This bypasses the "Welcome" wizard and sets up a user "Bolt"
    page = context.new_page()
    page.goto("http://localhost:8000")

    page.evaluate("""() => {
        localStorage.setItem('tytax_users_list', '["Bolt"]');
        localStorage.setItem('tytax_user_profile_Bolt', '{"name":"Bolt","bodyweight":80}');
    }""")

    page.reload()

    # Login as Bolt
    # The text might be "Bolt" in italics/bold, let's look for the button content
    # or just use text="Bolt" which is fuzzy match
    try:
        page.get_by_text("Bolt", exact=True).click()
    except:
        print("Could not find Bolt button directly, trying role")
        # In the FamilyManager: <span ...>{u}</span>
        page.locator("button", has_text="Bolt").click()

    # Navigate to Arsenal (Nav bar button)
    # Label is "ARSENAL" uppercase in UI (css text-transform?), but code says t('nav.arsenal') which defaults to Arsenal
    # The button has text "Arsenal" or "ARSENAL" depending on CSS.
    # text-transform: uppercase is used. Playwright matches visible text usually.
    page.get_by_role("button", name="Arsenal").click()

    # Wait for list to render
    page.wait_for_timeout(2000)

    # Check if exercises are visible
    # Look for "Chest" or specific muscle tags which rely on getImpact
    # Impact dots: "Chest (sternal pec)" etc.

    # Take screenshot
    if not os.path.exists("verification"):
        os.makedirs("verification")
    page.screenshot(path="verification/arsenal_view.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
