import os
import time
from playwright.sync_api import sync_playwright

def verify_fixes():
    with sync_playwright() as p:
        # Use mobile viewport to access Settings button
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 375, "height": 812})
        page = context.new_page()

        # Load the app
        cwd = os.getcwd()
        page.goto(f"file://{cwd}/index.html")

        # --- 1. Verify DoS Vulnerability ---
        print("Testing DoS Vulnerability...")

        # Bypass wizard & setup environment
        page.evaluate("""() => {
            localStorage.setItem('tytax_logs', '[]');
            localStorage.setItem('tytax_session_order', '["Upper A"]');
            localStorage.setItem('tytax_user_profile', JSON.stringify({name: "Tester", units: "KG", bodyweight: 80}));
        }""")
        page.reload()

        # Navigate to Settings (Mobile Header Button)
        page.get_by_label("Settings").click()

        # Prepare to catch dialogs
        def handle_dialog(dialog):
            print(f"Dialog message: {dialog.message}")
            dialog.accept()
        page.on("dialog", handle_dialog)

        # Upload malicious file
        file_input = page.locator("input[type='file']")
        try:
            file_input.set_input_files("poc_crash.json")
            print("File uploaded.")
        except Exception as e:
            print(f"Upload failed: {e}")

        # Wait for processing
        time.sleep(1)

        # Verify if app crashed on reload
        try:
            page.reload()
            time.sleep(1)
            # Check for crash screen
            if page.get_by_text("System Failure").is_visible():
                print("CRITICAL: App crashed after reload (Vulnerable!)")
            else:
                print("App loaded successfully (Verification passed: No crash loop)")

        except Exception as e:
            print(f"Page failed to reload: {e}")

        # --- 2. Verify Storage Quota Warning ---
        print("\nTesting Storage Quota...")

        # Reset page state
        page.goto(f"file://{cwd}/index.html")
        page.evaluate("""() => {
            localStorage.setItem('tytax_logs', '[]');
            localStorage.setItem('tytax_session_order', '["Upper A"]');
            localStorage.setItem('tytax_user_profile', JSON.stringify({name: "Tester", units: "KG", bodyweight: 80}));
        }""")
        page.reload()

        # Inject mock for localStorage.setItem
        page.evaluate("""() => {
             const originalSetItem = localStorage.setItem;
             localStorage.setItem = function(key, value) {
                if (key === 'tytax_logs' || key === 'tytax_oled_mode') {
                    throw new DOMException('The quota has been exceeded.', 'QuotaExceededError');
                }
                originalSetItem.call(localStorage, key, value);
            };
        }""")

        # Trigger save
        page.get_by_label("Settings").click()

        # Toggle OLED mode
        page.locator("button").filter(has=page.locator("div.rounded-full")).click()

        time.sleep(1)
        page.screenshot(path="verification/storage_test.png")
        print("Storage test screenshot saved.")

        # Check for toast
        toast = page.locator("div.fixed.top-24").first
        if toast.is_visible():
            print(f"Toast visible: {toast.inner_text()}")
        else:
            print("No toast detected (Vulnerable!)")

        browser.close()

if __name__ == "__main__":
    verify_fixes()
