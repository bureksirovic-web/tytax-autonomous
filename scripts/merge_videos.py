import json
import re
import os

def load_js_object(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Strip window.TYTAX_MAINFRAME = and ;
    json_str = content.replace('window.TYTAX_MAINFRAME = ', '').strip().rstrip(';')
    return json.loads(json_str)

def load_master_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Index by t1x_number
    return {item.get('t1x_number'): item for item in data}

def merge():
    mainframe_path = 'mainframe_library.js'
    master_json_path = '/tmp/file_attachments/tytax-exercises-full/tytax_t1x_exercises_full.json'
    output_path = 'full_exercises_final.js'

    print(f"Loading {mainframe_path}...")
    mainframe = load_js_object(mainframe_path)

    print(f"Loading {master_json_path}...")
    master = load_master_data(master_json_path)

    updated_count = 0

    for ex in mainframe:
        note = ex.get('note', '')
        if not note:
            continue

        # Extract t1x_number
        match = re.search(r't1x_number=(\d+)', note)
        if match:
            t1x_id = int(match.group(1))
            if t1x_id in master:
                m_data = master[t1x_id]
                videos = []

                # Map videos
                mappings = [
                    ('exercise_video_horizontal_url', 'Exercise (Landscape)'),
                    ('exercise_video_vertical_url', 'Exercise (Portrait)'),
                    ('instruction_video_horizontal_url', 'Instruction (Landscape)'),
                    ('instruction_video_vertical_url', 'Instruction (Portrait)'),
                    # Also check for 'exercise_video_other' if needed, but sticking to standard
                ]

                for key, label in mappings:
                    url = m_data.get(key, '').strip()
                    if url:
                        # Ensure URL is valid (basic check)
                        if url.startswith('http'):
                            videos.append({'url': url, 'label': label})

                if videos:
                    ex['videos'] = videos
                    updated_count += 1
            else:
                print(f"Warning: ID {t1x_id} not found in master data (Exercise: {ex['name']})")

    print(f"Updated {updated_count} exercises with video data.")

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("window.TYTAX_MAINFRAME = ")
        json.dump(mainframe, f, indent=2)
        f.write(";")

    print(f"Written to {output_path}")

if __name__ == "__main__":
    merge()
