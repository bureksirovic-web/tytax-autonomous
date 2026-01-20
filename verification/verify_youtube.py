import os
import json
import urllib.parse
from playwright.sync_api import sync_playwright

def verify_youtube_search(page):
    username = "TestUser"
    users = [username]
    profile = {
        "name": username,
        "bodyweight": 80,
        "gender": "male",
        "experience": "intermediate"
    }
    test_exercise = {
        "name": "Test No Video Exercise",
        "station": "Tytax",
        "muscle_group": "CHEST",
        "pattern": "Press",
        "unilateral": False,
        "sets": 3,
        "reps": "10",
        "videos": [],
        "impact": []
    }
    master_exercises = [test_exercise]

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

    # Go to Arsenal - Use .first() or specific selector to avoid strict mode violation
    # The desktop sidebar button is likely the first one visible or distinct.
    # We can filter by visibility or just use the button role

    # Desktop button
    page.get_by_role("button", name="Arsenal").first.click()

    page.wait_for_selector("text=Requisition New Intel", timeout=5000)

    # Check for the link
    expected_query = urllib.parse.quote(test_exercise["name"])

    # Locator for the link
    link = page.locator(f"a[href*='youtube.com/results?search_query={expected_query}']")

    # Wait for it to be visible
    link.wait_for(state="visible", timeout=5000)

    print("YouTube link found and visible.")

    # Screenshot
    page.screenshot(path="verification/verification_youtube_search.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use a larger viewport to ensure desktop mode (sidebar visible)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        try:
            verify_youtube_search(page)
            print("Verification Successful")
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/error.png")
            raise e
        finally:
            browser.close()
