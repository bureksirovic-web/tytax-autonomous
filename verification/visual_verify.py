
from playwright.sync_api import sync_playwright
import time

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()

    # 1. Inject State to bypass welcome
    context.add_init_script("""
        localStorage.setItem('tytax_user_profile', JSON.stringify({ name: 'Test User' }));
        localStorage.setItem('tytax_logs', '[]');
    """)

    page = context.new_page()

    # 2. Go to Index
    page.goto('file://' + '/app/index.html')

    # 3. Go to Builder
    page.click('button:has-text("Builder")')

    # 4. Create 6-Day PPL
    page.click('button:has-text("6")')
    page.click('button:has-text("Push / Pull / Legs")')

    # 5. Open "Push A"
    page.click('text="Push A"')

    # 6. Click Chest Filter to trigger potential bug
    page.click('button:has-text("CHEST")')

    # 7. Take Screenshot of Push A (Should NOT show Quads)
    page.screenshot(path='/app/verification/verification_push.png')

    # 8. Go Back and Open Pull A
    page.click('button:has-text("Back")')
    page.click('text="Pull A"')

    # 9. Take Screenshot of Pull A (Should SHOW Hamstrings/Glutes, HIDE Chest/Tri)
    page.screenshot(path='/app/verification/verification_pull.png')

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
