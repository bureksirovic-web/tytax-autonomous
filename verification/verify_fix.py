from playwright.sync_api import sync_playwright
import os

def test_fix(page):
    # 1. Arrange: Inject localStorage state to simulate the issue
    # We need to simulate the state where "Smith Flat Bench Press" is in masterExercises, has impact data, but NO note.
    # If the fix works, no popup should appear.

    mock_data = """
    [
        {
            "name": "TYTAX T1 | Smith Flat Bench Press",
            "station": "Smith Machine",
            "muscle_group": "CHEST",
            "pattern": "Horizontal Press",
            "unilateral": false,
            "sets": 3,
            "reps": "6-10",
            "impact": [{"m": "Chest", "s": 95}]
        }
    ]
    """

    # We need to set localStorage BEFORE the page loads the app logic
    page.add_init_script(f"""
        localStorage.setItem('tytax_master_exercises', '{mock_data}');
        localStorage.setItem('tytax_logs', '[]');
        localStorage.setItem('tytax_session_order', '[]');
        localStorage.setItem('tytax_training_plan', '{{}}');
    """)

    # 2. Act: Load the page
    # Using file:// protocol since it's a static HTML file
    cwd = os.getcwd()
    page.goto(f"file://{cwd}/index.html")

    # 3. Assert: Check for popup
    # If the popup appears, it's a failure. If it doesn't, success.
    # The popup is a window.confirm(). Playwright auto-dismisses dialogs by default,
    # but we can listen for it.

    dialog_triggered = False
    def handle_dialog(dialog):
        nonlocal dialog_triggered
        print(f"Dialog appeared: {dialog.message}")
        dialog_triggered = True
        dialog.accept()

    page.on("dialog", handle_dialog)

    # Wait a bit for the effect to run
    page.wait_for_timeout(2000)

    if dialog_triggered:
        print("FAILURE: Popup appeared despite fix.")
    else:
        print("SUCCESS: No popup appeared.")

    # 4. Screenshot
    page.screenshot(path="verification/popup_check.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        try:
            test_fix(page)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()
