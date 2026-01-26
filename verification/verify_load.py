
from playwright.sync_api import sync_playwright
import time

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Navigate to the app
    page.goto("http://localhost:8000/index.html")

    # Inject localStorage to simulate an existing user
    page.evaluate("""() => {
        const userProfile = { name: "BoltUser", bodyweight: 80, goal: "Speed" };
        localStorage.setItem('tytax_users_list', JSON.stringify(["BoltUser"]));
        localStorage.setItem('tytax_user_profile_BoltUser', JSON.stringify(userProfile));
        // Also set master exercises to ensure we have data to process with getImpact
        // We rely on the app default loading, but force a reload to pick up storage
    }""")

    # Reload to apply storage
    page.reload()

    # Click on the user "BoltUser" to log in
    # The login button text is the username
    page.get_by_text("BoltUser").click()

    # Wait for the dashboard to load. "System" or "Status" is likely visible.
    page.wait_for_selector("text=System")

    # Take a screenshot
    page.screenshot(path="verification/dashboard_loaded.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
