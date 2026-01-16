import os
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 375, "height": 812})
    page = context.new_page()
    cwd = os.getcwd()
    url = f"file://{cwd}/index.html"

    print(f"Navigating to {url}")
    page.goto(url)

    # 1. Complete Welcome Wizard (Step 1)
    print("Completing Wizard Step 1...")
    page.get_by_placeholder("Captain's Name").fill("Tester")
    page.get_by_text("Next Step").click()

    # Step 2: Bodyweight?
    print("Completing Wizard Step 2...")
    # Just assume it asks for bodyweight or something.
    # Let's check the code if possible or just use generic button clicks.
    # Step 2 usually is Bodyweight.
    # If I just click the button "Initialize System" or "Complete".
    # I'll wait for the next button.

    # Try to find "Initialize" or similar.
    # Actually, Step 2 is likely bodyweight.
    try:
        page.get_by_placeholder("KG").fill("80") # Maybe?
        page.get_by_role("button").last.click() # Click whatever is there
    except:
        pass

    # Wait for "Initialize" button eventually?
    # Or just inject LS now that we know we were stuck.

    # Actually, I'll go back to LS injection but being smarter about it.
    # The previous injection failed because I didn't set everything needed.

    browser.close()

def run_injected(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 375, "height": 812})

    # Full Injection
    context.add_init_script("""
        const profile = {name: "Commander", bodyweight: 80};
        const logs = [];
        const master = [
            {
                name: "Test Press",
                station: "Smith Machine",
                muscle_group: "CHEST",
                pattern: "Press",
                sets: 3,
                reps: "8-12",
                impact: [{muscle: "Chest", score: 100}]
            },
            {
                name: "Test Pull",
                station: "Lat Pulldown",
                muscle_group: "BACK",
                pattern: "Pull",
                sets: 3,
                reps: "8-12",
                impact: [{muscle: "Lats", score: 100}]
            }
        ];
        const plan = {"Test Day": ["Test Press", "Test Pull"]};
        const order = ["Test Day"];

        localStorage.setItem('tytax_user_profile', JSON.stringify(profile));
        localStorage.setItem('tytax_logs', JSON.stringify(logs));
        localStorage.setItem('tytax_master_exercises', JSON.stringify(master));
        localStorage.setItem('tytax_training_plan', JSON.stringify(plan));
        localStorage.setItem('tytax_session_order', JSON.stringify(order));
    """)

    page = context.new_page()
    cwd = os.getcwd()
    url = f"file://{cwd}/index.html"
    page.goto(url)

    # 2. Go to Gym
    print("Navigating to Gym...")
    page.get_by_text("Gym").locator("visible=true").click()

    # 3. Start Workout
    print("Starting Workout...")
    page.get_by_text("Engage Lift").click()

    # 4. Verify UI Elements
    print("Verifying UI...")
    page.wait_for_selector("text=Target:")

    print("Taking screenshot...")
    page.screenshot(path="verification/verification_mobile.png", full_page=True)

    browser.close()
    print("Done.")

with sync_playwright() as playwright:
    run_injected(playwright)
