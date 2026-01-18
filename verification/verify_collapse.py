from playwright.sync_api import sync_playwright
import os
import json

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        cwd = os.getcwd()
        page.goto(f'file://{cwd}/index.html')

        plan = {
            "Upper A": ["TYTAX T1 | Smith Flat Bench Press"]
        }

        master_exercises = [
            {
                "name": "TYTAX T1 | Smith Flat Bench Press",
                "station": "Smith Machine",
                "sets": 3,
                "reps": "10",
                "impact": [{"m": "Chest", "s": 100}],
                "videos": [{"url": "http://example.com", "label": "Test"}]
            }
        ]

        page.evaluate(f'''() => {{
            localStorage.setItem('tytax_user_profile', JSON.stringify({{name: 'Test User', bodyweight: 80}}));
            localStorage.setItem('tytax_session_order', JSON.stringify(['Upper A']));
            localStorage.setItem('tytax_training_plan', JSON.stringify({json.dumps(plan)}));
            localStorage.setItem('tytax_master_exercises', JSON.stringify({json.dumps(master_exercises)}));
        }}''')

        page.reload()

        # Start Workout
        page.get_by_text('ENTER TRAINING CENTER').click()
        page.get_by_role('button', name='Upper A').click()
        page.get_by_text('ENGAGE LIFT').click()

        # 1. Initial State
        page.wait_for_selector('text=Smith Flat Bench Press')
        page.screenshot(path='verification/1_expanded.png')

        # 6. Verify Stop Propagation on Action Buttons (Video)
        video_btn = page.locator('#exercise-card-0 a:has(svg polygon)')
        if video_btn.count() > 0:
            try:
                with page.context.expect_page(timeout=5000) as new_page_info:
                    video_btn.click()
            except:
                pass # Popup might be blocked or handled differently, main goal is check collapse

            page.wait_for_timeout(500)
            # Check if card is still expanded
            if page.locator('text=Smith Flat Bench Press').is_visible():
                print("Video click: Card remained expanded (Success)")
                page.screenshot(path='verification/5_video_click_no_collapse.png')
            else:
                print("Video click: Card collapsed (Failure)")
                exit(1)
        else:
            print("Video button not found")

        # 2. Complete Sets
        for i in range(3):
            page.fill(f'#input-kg-0-{i}', '20')
            page.fill(f'#input-reps-0-{i}', '10')
            page.locator('#exercise-card-0 button.col-span-2').nth(i).click()
            page.wait_for_timeout(200)

        # 3. Auto-Collapse
        try:
            page.wait_for_selector('text=3/3 Done', timeout=5000)
            page.screenshot(path='verification/2_collapsed.png')
            print("Auto-collapse: Success")
        except:
            print("Auto-collapse: Failure")
            page.screenshot(path='verification/2_failed.png')
            exit(1)

        # 4. Manual Expand
        page.locator('#exercise-card-0').click()
        page.wait_for_selector('text=Smith Flat Bench Press')
        page.screenshot(path='verification/3_reopened.png')

        # 5. Manual Collapse via Header
        page.locator('h3:has-text("Smith Flat Bench Press")').click()
        try:
            page.wait_for_selector('text=3/3 Done', timeout=5000)
            page.screenshot(path='verification/4_manual_collapsed.png')
            print("Manual collapse: Success")
        except:
            print("Manual collapse: Failure")
            exit(1)

        browser.close()

if __name__ == '__main__':
    run()
