
import os
from playwright.sync_api import sync_playwright

def verify_arsenal():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()

        cwd = os.getcwd()
        file_path = f'file://{cwd}/index.html'

        page.goto(file_path)

        # Inject
        page.evaluate("""
            localStorage.setItem('tytax_users_list', '["TestUser"]');
            localStorage.setItem('tytax_user_profile_TestUser', '{"name":"TestUser", "bodyweight": 80}');
            localStorage.setItem('tytax_logs_TestUser', '[]');
        """)
        page.reload()

        page.click('button:has-text("TestUser")')
        page.wait_for_selector('text=TYTAX ELITE', timeout=10000)

        page.click('aside nav button:has-text("Arsenal")')

        # Relaxed selector
        page.wait_for_selector('text=Arsenal', timeout=5000)
        page.wait_for_selector('text=Database', timeout=5000)

        screenshot_path = 'verification/arsenal_verified.png'
        page.screenshot(path=screenshot_path)
        print(f'Screenshot saved to {screenshot_path}')

        browser.close()

if __name__ == '__main__':
    verify_arsenal()
