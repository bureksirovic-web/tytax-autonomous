import os
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 414, 'height': 896}) # Mobile view
    page = context.new_page()

    # Get absolute path to index.html
    cwd = os.getcwd()
    file_path = f"file://{cwd}/index.html"

    # Inject LocalStorage BEFORE loading to bypass wizards
    # We simulate a logged-in user "Tester"
    page.goto(file_path)

    page.evaluate("""() => {
        localStorage.setItem('tytax_users_list', JSON.stringify(['Tester']));
        localStorage.setItem('tytax_user_profile_Tester', JSON.stringify({name: 'Tester', bodyweight: 80}));
        localStorage.setItem('tytax_language', 'en');
        // We do NOT inject tytax_master_exercises_Tester, so it defaults to PRESETS[0]
    }""")

    # Reload to apply storage
    page.reload()

    # 1. Login (Click "Tester")
    page.get_by_role("button", name="Tester").click()

    # 2. Go to Arsenal Tab
    page.get_by_role("button", name="Arsenal").click()

    # 3. Search for "Smith Flat Bench Press"
    page.get_by_placeholder("Search Operations...").fill("Smith Flat Bench Press")

    # 4. Wait for results
    page.wait_for_timeout(1000)

    # 5. Take screenshot of the card
    page.screenshot(path="verification/arsenal_video_check.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
