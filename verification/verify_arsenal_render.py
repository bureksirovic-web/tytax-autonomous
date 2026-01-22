import os
import json
from playwright.sync_api import sync_playwright

def verify_arsenal_render(page):
    username = "BoltUser"
    users = [username]
    profile = {
        "name": username,
        "bodyweight": 80
    }

    # Test cases for getImpact
    ex_array = {
        "name": "Bench Press Array",
        "station": "Tytax",
        "sets": 3,
        "impact": [{"m": "Chest", "s": 100}]
    }
    ex_object = {
        "name": "Bench Press Object",
        "station": "Tytax",
        "sets": 3,
        "impact": {"Chest": 100}
    }
    ex_note = {
        "name": "Bench Press Note",
        "station": "Tytax",
        "sets": 3,
        "note": "Primary Chest 100"
    }

    master_exercises = [ex_array, ex_object, ex_note]

    file_path = f"file://{os.getcwd()}/index.html"
    page.goto(file_path)

    page.evaluate(f"""() => {{
        localStorage.clear();
        localStorage.setItem('tytax_users_list', '{json.dumps(users)}');
        localStorage.setItem('tytax_user_profile_{username}', '{json.dumps(profile)}');
        localStorage.setItem('tytax_master_exercises_{username}', '{json.dumps(master_exercises)}');
        localStorage.setItem('tytax_language_{username}', 'en');
        localStorage.setItem('tytax_logs_{username}', '[]');
    }}""")

    page.reload()

    # Login
    page.get_by_text(username).click()
    page.wait_for_selector("text=System Status", timeout=10000)

    # Go to Arsenal
    page.get_by_role("button", name="Arsenal").first.click()

    # Verify Arsenal Header
    page.wait_for_selector("text=Arsenal", timeout=5000)

    # Verify Exercises are rendered
    page.wait_for_selector("text=Bench Press Array", timeout=5000)
    page.wait_for_selector("text=Bench Press Object", timeout=5000)
    page.wait_for_selector("text=Bench Press Note", timeout=5000)

    print("Arsenal rendered correctly with all impact formats.")
    page.screenshot(path="verification/arsenal_render.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        try:
            verify_arsenal_render(page)
            print("Verification Successful")
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/error_arsenal.png")
            raise e
        finally:
            browser.close()
