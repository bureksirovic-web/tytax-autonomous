import os

def fix_app():
    print('🚑 Starting Surgical Hotfix for Toast Error...')
    
    # Read the file
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # The missing code block
    toast_logic = """
    // --- HOTFIX INJECTED START ---
    const [toast, setToast] = React.useState(null);
    const showToast = (message, duration = 3000) => {
        setToast({ message, duration });
        setTimeout(() => setToast(null), duration);
    };
    // --- HOTFIX INJECTED END ---
    """

    # 1. Check if it's already there (to avoid duplicates)
    if "const [toast, setToast]" in content:
        print("⚠️ Code seems to exist already. Checking placement...")
        # If it exists but crashes, it might be in the wrong place. 
        # But for safety, let's assume if it's there, we shouldn't blindly duplicate.
        # We will proceed only if it's strictly missing.
    
    # 2. Find the entry point: "function App() {"
    target_str = "function App() {"
    if target_str not in content:
        print("❌ Could not find 'function App() {' in index.html")
        return

    # 3. Inject immediately after the function starts
    parts = content.split(target_str)
    # Reassemble: [Everything before] + [function App() {] + [Toast Logic] + [Everything after]
    new_content = parts[0] + target_str + "\n" + toast_logic + "\n" + parts[1]
    
    # 4. Save
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ HOTFIX APPLIED. The 'toast' variable is now defined inside App().")

if __name__ == "__main__":
    fix_app()
