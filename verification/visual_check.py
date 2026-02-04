from playwright.sync_api import sync_playwright
import os

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        # Load page
        cwd = os.getcwd()
        page.goto(f"file://{cwd}/index.html")

        # Inject user data to bypass wizard
        page.evaluate("""() => {
            localStorage.setItem('tytax_users_list', '["Bolt"]');
            localStorage.setItem('tytax_user_profile_Bolt', JSON.stringify({
                name: "Bolt",
                gender: "Male",
                bodyweight: 80,
                experience: "Advanced"
            }));
            localStorage.setItem('tytax_logs_Bolt', '[]');
        }""")

        # Reload to apply storage
        page.reload()

        # Click user to login
        try:
            page.get_by_text("Bolt").click(timeout=5000)
        except Exception as e:
            print("Failed to click Bolt user")
            page.screenshot(path="verification/fail_login.png")
            raise e

        # Click Arsenal tab
        try:
            page.get_by_text("Arsenal").first.click(timeout=5000)
        except Exception as e:
            print("Failed to click Arsenal tab")
            page.screenshot(path="verification/fail_tab.png")
            raise e

        # Wait for the search input to be visible
        try:
            search_input = page.get_by_placeholder("Search Arsenal...")
            search_input.wait_for(state="visible", timeout=5000)
            search_input.fill("Bench")
        except Exception as e:
            print("Failed to find Search Arsenal input")
            page.screenshot(path="verification/fail_search.png")
            raise e

        # Wait a bit for debounce and render
        page.wait_for_timeout(2000)

        # Screenshot
        page.screenshot(path="verification/visual_check.png")
        print("Screenshot saved to verification/visual_check.png")

        browser.close()

if __name__ == "__main__":
    run()
