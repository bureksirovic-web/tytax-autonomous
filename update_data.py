import json
import re

def update_data():
    # Read the JSON file
    with open('tytax_t1_exercise_library_v1_1.json', 'r') as f:
        new_data = json.load(f)

    # Read the HTML file
    with open('index.html', 'r') as f:
        html_content = f.read()

    # Locate the PRESETS definition
    # We are looking for the 'kinetic_impact' preset
    # Pattern to find the start of the PRESETS array and the kinetic_impact object
    
    # We will use regex to find the PRESETS array content.
    # However, since we need to preserve INITIAL_PLAN and INITIAL_ORDER inside kinetic_impact,
    # and replace MASTER_EXERCISES, MUSCLE_GROUPS, STATIONS, RECOMMENDED_ATTACHMENTS,
    # it's safer to reconstruct the data object for kinetic_impact.

    # Let's extract the PRESETS string first using a simpler approach if possible,
    # or just parse the JS object? No, it's inside a <script> tag.
    
    # Let's target the specific block inside `const PRESETS = [ ... ]`
    
    # Regex to find the 'kinetic_impact' object
    # It starts with { id: "kinetic_impact", ... data: { ... } }
    
    # Actually, the file structure is quite consistent.
    # We can search for `data: {` inside the `kinetic_impact` block.
    
    # Let's try to extract the existing 'kinetic_impact' data block.
    # We can search for the "data": { ... } block following "kinetic_impact".
    
    # Find the start of PRESETS
    presets_start_match = re.search(r'const PRESETS = \[\s*\{', html_content)
    if not presets_start_match:
        print("Could not find PRESETS")
        return

    # To ensure we are editing the right place, let's look for "kinetic_impact"
    # and then the "data" key.
    
    # We know the structure:
    # id: "kinetic_impact",
    # name: ...,
    # description: ...,
    # data: {
    #   "MUSCLE_GROUPS": [...],
    #   "STATIONS": [...],
    #   "RECOMMENDED_ATTACHMENTS": [...],
    #   "MASTER_EXERCISES": [...],
    #   "INITIAL_PLAN": { ... },
    #   "INITIAL_ORDER": [ ... ]
    # }
    
    # We want to replace MUSCLE_GROUPS, STATIONS, RECOMMENDED_ATTACHMENTS, MASTER_EXERCISES
    # with data from `new_data`.
    # And keep INITIAL_PLAN and INITIAL_ORDER from the existing file.

    # 1. Extract the existing INITIAL_PLAN and INITIAL_ORDER using regex
    # Be careful with nested braces.
    
    # Finding INITIAL_PLAN
    plan_match = re.search(r'"INITIAL_PLAN":\s*(\{.*?\})\s*,', html_content, re.DOTALL)
    # The regex above is risky because of nested braces in INITIAL_PLAN (lists inside).
    # Better approach:
    # Read the file line by line? Or utilize the fact that we have the file content.
    
    # Let's grab the content of INITIAL_PLAN manually or use a more robust regex if the format is consistent.
    # In the file provided:
    # "INITIAL_PLAN": {
    #    "Upper A": [ ... ],
    #    ...
    # },
    
    # Let's find the start index of "INITIAL_PLAN":
    idx_plan = html_content.find('"INITIAL_PLAN":')
    if idx_plan == -1:
        print("Could not find INITIAL_PLAN")
        return
        
    # Count braces to find the end of the object
    idx_start_brace = html_content.find('{', idx_plan)
    brace_count = 1
    idx_current = idx_start_brace + 1
    while brace_count > 0:
        if html_content[idx_current] == '{':
            brace_count += 1
        elif html_content[idx_current] == '}':
            brace_count -= 1
        idx_current += 1
    
    initial_plan_str = html_content[idx_start_brace:idx_current]
    
    # finding INITIAL_ORDER
    idx_order = html_content.find('"INITIAL_ORDER":')
    if idx_order == -1:
        print("Could not find INITIAL_ORDER")
        return
        
    idx_start_bracket = html_content.find('[', idx_order)
    bracket_count = 1
    idx_current_order = idx_start_bracket + 1
    while bracket_count > 0:
        if html_content[idx_current_order] == '[':
            bracket_count += 1
        elif html_content[idx_current_order] == ']':
            bracket_count -= 1
        idx_current_order += 1
        
    initial_order_str = html_content[idx_start_bracket:idx_current_order]

    # Now construct the new data object body
    # We will format the new data as JSON strings, but we need to indent them to match the file style if possible,
    # or just dump them. The file uses 2 spaces or similar.
    
    # Prepare the new sections
    muscle_groups_json = json.dumps(new_data['MUSCLE_GROUPS'], indent=2)
    stations_json = json.dumps(new_data['STATIONS'], indent=2)
    attachments_json = json.dumps(new_data['RECOMMENDED_ATTACHMENTS'], indent=2)
    master_exercises_json = json.dumps(new_data['MASTER_EXERCISES'], indent=2)
    
    # Construct the replacement string for the `data` object content
    # We are replacing everything inside `data: { ... }` for kinetic_impact
    
    new_data_content = f'''
                  "MUSCLE_GROUPS": {muscle_groups_json},
                  "STATIONS": {stations_json},
                  "RECOMMENDED_ATTACHMENTS": {attachments_json},
                  "MASTER_EXERCISES": {master_exercises_json},
                  "INITIAL_PLAN": {initial_plan_str},
                  "INITIAL_ORDER": {initial_order_str}
                '''
    
    # Locate the start and end of the `data` object in existing HTML
    # It starts after `data: {` inside `kinetic_impact`
    
    # Locate "id": "kinetic_impact"
    idx_id = html_content.find('id: "kinetic_impact"')
    if idx_id == -1:
        print("Could not find kinetic_impact ID")
        return
        
    # Find `data: {` after that
    idx_data_start = html_content.find('data: {', idx_id)
    if idx_data_start == -1:
        print("Could not find data start")
        return
        
    idx_open_brace = idx_data_start + 6 # len('data: ') is 6, pointing to {
    
    # Find the matching closing brace for `data`
    brace_count = 1
    idx_current = idx_open_brace + 1
    while brace_count > 0:
        if html_content[idx_current] == '{':
            brace_count += 1
        elif html_content[idx_current] == '}':
            brace_count -= 1
        idx_current += 1
    
    idx_data_end = idx_current - 1 # Points to the closing }
    
    # Replace the content inside `data: { ... }`
    # Note: `new_data_content` does not include the outer braces, so we insert it between idx_open_brace+1 and idx_data_end
    
    updated_html = html_content[:idx_open_brace+1] + new_data_content + html_content[idx_data_end:]
    
    with open('index.html', 'w') as f:
        f.write(updated_html)

if __name__ == "__main__":
    update_data()
