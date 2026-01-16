from playwright.sync_api import sync_playwright
import os

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Force desktop viewport
        page = browser.new_page(viewport={'width': 1280, 'height': 720})

        file_path = os.path.abspath('index.html')

        # Bypass Welcome Wizard
        page.add_init_script("""
            localStorage.setItem('tytax_user_profile', JSON.stringify({name: 'Commander', units: 'KG', bodyweight: 100}));
            localStorage.setItem('tytax_logs', '[]');
            // Also need to ensure a protocol is loaded so 'System Standby' doesn't block things?
            // Actually System Standby is on the Home tab, but we want to navigate.
            // Let's also load the default protocol just in case.
            // But the app code initializes with kinetic_impact if customProtocols is empty?
            // No, setLibrary initializes from PRESETS[0].
            // sessionOrder is loaded from localStorage. If empty, it's Standby.
            // Let's seed sessionOrder too to be 'Online'.
            const preset = {
                'Upper A': ['Bench'], 'Lower A': ['Squat']
            };
            localStorage.setItem('tytax_training_plan', JSON.stringify(preset));
            localStorage.setItem('tytax_session_order', JSON.stringify(['Upper A', 'Lower A']));
        """)

        page.goto(f'file://{file_path}')

        # Give React a moment to hydrate and hide the wizard
        page.wait_for_timeout(500)

        # Now click Manual
        try:
            print('Clicking Manual sidebar button...')
            page.get_by_role('button', name='Manual').click()
        except Exception as e:
            print(f'Sidebar click failed: {e}')
            print('Clicking System Guide...')
            page.get_by_role('button', name='System Guide').click()

        page.wait_for_timeout(1000)

        page.screenshot(path='verification/manual_verification.png', full_page=True)
        browser.close()

if __name__ == '__main__':
    run()
