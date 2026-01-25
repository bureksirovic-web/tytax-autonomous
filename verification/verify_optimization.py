
import os
from playwright.sync_api import sync_playwright

def verify_optimization():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to app
        page.goto("http://localhost:8000")

        # Inject user profile to bypass Welcome Wizard (Optimization from memory)
        page.evaluate("""() => {
            localStorage.setItem('tytax_users_list', JSON.stringify(['BoltUser']));
            localStorage.setItem('tytax_user_profile_BoltUser', JSON.stringify({ name: 'BoltUser', bodyweight: 80 }));
            window.location.reload();
        }""")

        # Wait for reload
        page.wait_for_load_state('networkidle')

        # Click user to login
        page.get_by_text("BoltUser").click()

        # Wait for Dashboard
        page.get_by_text("TYTAX ELITE").wait_for()

        # Open Mainframe (Requisition Intel)
        page.get_by_text("Requisition Intel").click()

        # Wait for modal
        page.get_by_text("TYTAX MAINFRAME").wait_for()

        # Type in search to trigger filtering (and thus getImpact)
        page.get_by_placeholder("Search Mainframe...").fill("Bench")

        # Wait a bit for debounce and render
        page.wait_for_timeout(1000)

        # Take screenshot
        page.screenshot(path="verification/mainframe_filtered.png")

        print("Screenshot taken.")
        browser.close()

if __name__ == "__main__":
    verify_optimization()
