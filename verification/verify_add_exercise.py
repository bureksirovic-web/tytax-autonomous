from playwright.sync_api import sync_playwright, expect
import json
import time

def verify_add_exercise():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        # Prepare valid data for localStorage to bypass wizards and standby
        # We need "Smith Flat Bench Press" in the master library to search for it.
        master_exercises = [
            {"name": "Smith Flat Bench Press", "station": "Smith Machine", "pattern": "Horizontal Press", "sets": 3},
            {"name": "Smith Back Squat", "station": "Smith Machine", "pattern": "Squat", "sets": 3}
        ]

        init_data = {
            "tytax_user_profile": json.dumps({"name": "Test User", "units": "KG", "bodyweight": 80}),
            "tytax_session_order": json.dumps(["Upper A", "Lower A"]),
            "tytax_training_plan": json.dumps({"Upper A": ["Smith Back Squat"], "Lower A": ["Smith Back Squat"]}),
            "tytax_master_exercises": json.dumps(master_exercises),
            "tytax_logs": "[]",
            "tytax_start_date": "2023-01-01"
        }

        # Create init script
        script = ""
        for k, v in init_data.items():
            # Escape single quotes in value just in case (JSON dumps handles it mostly but strictly speaking JS string)
            # safe_v = v.replace("'", "\\'") # JSON dumps uses double quotes so it's fine inside single quotes '...'
            script += f"window.localStorage.setItem('{k}', '{v}');"

        page = context.new_page()
        page.add_init_script(script)

        page.goto("http://localhost:8080")

        # 1. Navigate to Gym
        print("Navigating to Gym...")
        page.get_by_role("button", name="Gym").click()

        # 2. Start Workout (Engage Lift)
        print("Engaging lift...")
        # Since we pre-seeded session order, we should see the "Training Center" engage screen
        engage_btn = page.get_by_text("Engage Lift")
        expect(engage_btn).to_be_visible()
        engage_btn.click()

        # 3. Click Add Manual Exercise
        print("Clicking Add Manual Exercise...")
        add_btn = page.get_by_text("Add Manual Exercise")
        # Scroll to it
        add_btn.scroll_into_view_if_needed()
        add_btn.click()

        # 4. Verify Modal Open
        print("Verifying Modal...")
        expect(page.get_by_text("Manual Injection")).to_be_visible()

        # 5. Search
        print("Searching...")
        page.get_by_placeholder("Search library...").fill("Bench")

        # 6. Select Exercise
        print("Selecting Exercise...")
        # Wait for the list to update
        ex_btn = page.get_by_role("button").filter(has_text="Smith Flat Bench Press").first
        expect(ex_btn).to_be_visible()
        ex_btn.click()

        # 7. Verify Toast
        print("Verifying Toast...")
        expect(page.get_by_text("Exercise Added")).to_be_visible()

        # 8. Verify Exercise Added to List
        print("Verifying Exercise in List...")
        # It should be at the bottom.
        page.wait_for_timeout(500)

        # Find the exercise card.
        # Since our pre-seeded workout has "Smith Back Squat", and we added "Smith Flat Bench Press".
        # We expect "Smith Flat Bench Press" to be visible.
        bench_card = page.get_by_role("heading", name="Smith Flat Bench Press")
        bench_card.scroll_into_view_if_needed()
        expect(bench_card).to_be_visible()

        print("Taking Screenshot...")
        page.screenshot(path="verification/add_exercise_success.png")
        print("Verification Complete.")

        browser.close()

if __name__ == "__main__":
    verify_add_exercise()
