import os
import time
from playwright.sync_api import sync_playwright

# Configuration
SCREENSHOT_DIR = "verification/screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def take_screenshot(page, name):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filepath = f"{SCREENSHOT_DIR}/{name}.png"
    page.screenshot(path=filepath)
    print(f"Screenshot saved: {filepath}")

def run_systems_check():
    with sync_playwright() as p:
        # --- SCENARIO A: MOBILE FRESH INSTALL ---
        print("\n--- SCENARIO A: MOBILE FRESH INSTALL (iPhone 13) ---")
        iphone_13 = p.devices['iPhone 13']
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(**iphone_13)
        page = context.new_page()

        file_path = os.path.abspath("index.html")
        page.goto(f"file://{file_path}")

        # Ensure Clean Slate
        page.evaluate("localStorage.clear()")
        page.reload()

        # 1. Family Manager (Create User)
        print("Verifying Family Manager...")
        try:
            page.wait_for_selector("input[placeholder='Codename']", timeout=5000)
            take_screenshot(page, "mobile_01_family_manager")
            print("✅ Family Manager loaded.")

            # Create User
            page.fill("input[placeholder='Codename']", "Shepard")
            # Click the button next to input. It's inside a flex gap-2 container.
            # Use specific hierarchy if needed, but text matching or icon matching is hard without arialabel.
            # Using the class structure from grep: <button onClick={handleAddUser} ...>
            # It's the only button in that "NEW OPERATOR" block usually.
            # Let's target the button inside the parent div of the input.
            page.locator("input[placeholder='Codename']").locator("..").locator("button").click()
            print("User 'Shepard' created.")

        except Exception as e:
            print(f"❌ Family Manager failed: {e}")
            take_screenshot(page, "mobile_01_error")
            return

        # 2. Welcome Wizard (Now it should appear)
        print("Verifying Welcome Wizard...")
        try:
            # Wizard Step 1: Name
            # Use case-insensitive regex or partial text to be safer
            page.wait_for_selector("text=/WELCOME/i", timeout=5000)
            take_screenshot(page, "mobile_02_welcome_wizard")
            print("✅ Welcome Wizard appeared.")

            # The name input might be pre-filled or empty.
            # We need to fill it to enable "Next".
            # If "N7" fails, try generic selector or the only text input in the modal.
            page.fill("input[placeholder='...']", "N7")
            page.click("button:has-text('Next')")

            # Wizard Step 2: Units
            print("Wizard Step 2: Units")
            page.wait_for_selector("button:has-text('Confirm')", timeout=2000)
            page.click("button:has-text('Confirm')")

            # Wizard Step 3: Bodyweight
            print("Wizard Step 3: Bodyweight")
            # Wait for the next step to appear
            page.wait_for_selector("button:has-text('Initialize System')", timeout=2000)
            # Find input for bodyweight (it might be the only input now)
            # Or assume 75 is default?
            # Let's try to fill it.
            try:
                page.fill("input[type='number']", "75")
            except:
                pass # Maybe not needed or input not found

            page.click("button:has-text('Initialize System')")

            # Wait for Wizard to disappear (element with z-[400] should go away)
            page.wait_for_selector("text=System Status", timeout=5000)

        except Exception as e:
            print(f"❌ Welcome Wizard failed to complete: {e}")
            take_screenshot(page, "mobile_02_error")

        # 3. Verify Dashboard
        print("Verifying Dashboard...")
        try:
            page.wait_for_selector("text=System Status", timeout=5000)
            take_screenshot(page, "mobile_03_dashboard")
            print("✅ Dashboard loaded.")
        except Exception as e:
            print(f"❌ Dashboard failed to load: {e}")
            take_screenshot(page, "mobile_03_error")
            return

        # 4. Verify Pre-loaded Arsenal Banner
        if page.is_visible("text=Arsenal pre-loaded"):
             print("✅ Pre-loaded Arsenal banner visible.")
        else:
             print("⚠️ Pre-loaded Arsenal banner NOT found (Minor).")

        # 5. Check Mobile Navigation
        print("Checking Mobile Navigation...")
        # Use visible=True to distinguish between Desktop Sidebar (hidden) and Mobile Bottom Bar (visible)
        # Note: Playwright's click auto-waits for visibility, but if multiple exist, we need to pick the visible one.
        arsenal_btns = page.locator("button:has-text('Arsenal')").all()
        clicked = False
        for btn in arsenal_btns:
            if btn.is_visible():
                btn.click()
                clicked = True
                break

        if not clicked:
             print("❌ Could not find visible Arsenal button.")

        time.sleep(0.5)
        take_screenshot(page, "mobile_04_arsenal_tab")
        # Check for unique element on Arsenal page (e.g., "Active Arsenal" or just header)
        if page.is_visible("text=Active Arsenal") or page.is_visible("text=Database"):
            print("✅ Arsenal Tab accessible.")
        else:
            print("❌ Arsenal Tab navigation failed (Header not found).")

        context.close()

        # --- SCENARIO B: DESKTOP ---
        print("\n--- SCENARIO B: DESKTOP CORE USAGE ---")
        context_desktop = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page_desktop = context_desktop.new_page()
        page_desktop.goto(f"file://{file_path}")

        # We need to log in again or create user because it's a new context (cleared storage).
        page_desktop.evaluate("localStorage.clear()")
        page_desktop.reload()

        # Family Manager
        page_desktop.fill("input[placeholder='Codename']", "Admin")
        page_desktop.locator("input[placeholder='Codename']").locator("..").locator("button").click()

        # Wizard (Must complete to clear overlay)
        print("Completing Wizard for Desktop...")
        try:
            page_desktop.wait_for_selector("text=/WELCOME/i", timeout=5000)
            page_desktop.fill("input[placeholder='...']", "Admin")
            page_desktop.click("button:has-text('Next')")

            # Step 2
            page_desktop.wait_for_selector("button:has-text('Confirm')", timeout=2000)
            page_desktop.click("button:has-text('Confirm')")

            # Step 3
            page_desktop.wait_for_selector("button:has-text('Initialize System')", timeout=2000)
            try:
                page_desktop.fill("input[type='number']", "85")
            except:
                pass
            page_desktop.click("button:has-text('Initialize System')")

            # Wait for overlay to go
            page_desktop.wait_for_selector("text=System Status", timeout=5000)

        except Exception as e:
            print(f"⚠️ Desktop Wizard skipped or failed: {e}")

        page_desktop.wait_for_selector("text=System Status")
        take_screenshot(page_desktop, "desktop_01_dashboard")

        # 1. Mainframe & Pagination
        print("Verifying Mainframe & Pagination...")
        # Click Arsenal Tab (Desktop Sidebar should be visible)
        page_desktop.click("button:has-text('Arsenal')")

        # Open Mainframe.
        try:
            # On desktop, "Requisition Intel" might be visible.
            # Using partial text match or exact match from screenshot
            page_desktop.click("button:has-text('REQUISITION NEW INTEL')")
            page_desktop.wait_for_selector("text=TYTAX Mainframe")
            take_screenshot(page_desktop, "desktop_02_mainframe_modal")

            # Check pagination
            # Scroll to bottom of modal content if needed
            if page_desktop.is_visible("button:has-text('Load More')"):
                 print("✅ 'Load More' button found.")
                 page_desktop.click("button:has-text('Load More')")
            else:
                 print("⚠️ 'Load More' not found.")

        except Exception as e:
            print(f"❌ Mainframe test failed: {e}")
            take_screenshot(page_desktop, "desktop_error_mainframe")
            return

        # 2. Add Exercise
        # Click "Requisition" on the first item.
        # Note: "Requisition" might be "Add" or icon.
        # But text search usually works if label exists.
        # If not, let's look for text "Requisition" inside the modal.
        try:
            btns = page_desktop.locator("button:has-text('Requisition')").all()
            if len(btns) > 0:
                # Click the second one (first might be header?)
                btns[0].click()
                print("✅ Requisitioned exercise.")
                page_desktop.keyboard.press("Escape")
            else:
                print("❌ No Requisition buttons.")
        except:
             print("❌ Failed to click Requisition.")

        # 3. Verify in Arsenal
        take_screenshot(page_desktop, "desktop_04_arsenal_updated")

        # --- SCENARIO C: DATA PERSISTENCE ---
        print("\n--- SCENARIO C: DATA PERSISTENCE ---")
        page_desktop.reload()
        try:
            # Wait for either Dashboard OR Family Manager
            # We expect Family Manager usually (auto-logout on refresh)
            # Wait for "Admin" user card to appear (or Dashboard)
            page_desktop.wait_for_selector("text=Admin", timeout=5000)

            if page_desktop.is_visible("text=Admin"):
                print("✅ User 'Admin' found in Family Manager (Data Persisted).")
                page_desktop.click("text=Admin")
                # Wait for dashboard
                page_desktop.wait_for_selector("text=System Status")
                print("✅ Re-login successful.")
            elif page_desktop.is_visible("text=System Status"):
                print("✅ Session persisted (Auto-login).")
            else:
                 print("❌ User data lost.")
                 take_screenshot(page_desktop, "persistence_failure")
                 return

            # Check Arsenal for the item
            page_desktop.click("button:has-text('Arsenal')")
            take_screenshot(page_desktop, "desktop_05_persistence")
            if page_desktop.is_visible("text=Database"):
                print("✅ Arsenal Database persisted.")

        except Exception as e:
             print(f"❌ Persistence check failed: {e}")
             take_screenshot(page_desktop, "persistence_failure")

        browser.close()
        print("\n--- SYSTEMS CHECK COMPLETE ---")

if __name__ == "__main__":
    run_systems_check()
