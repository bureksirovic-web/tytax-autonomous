import json
import uuid
import datetime
import random

def generate_log_entry(day_index):
    # Simulate a typical session
    exercises = []
    # 6 exercises per session (average)
    for i in range(6):
        sets = []
        # 3 working sets + 2 warmups
        for j in range(5):
            sets.append({
                "kg": "100.5",
                "reps": "12",
                "rir": "2",
                "done": True,
                "type": "working" if j > 1 else "warmup"
            })

        exercises.append({
            "name": f"Exercise Name {i}",
            "station": "Smith Machine",
            "unilateral": False,
            "impact": [{"m": "Chest", "s": 90}],
            "targetReps": "8-12",
            "note": "Keep elbows tucked",
            "sets": sets
        })

    entry = {
        "id": str(uuid.uuid4()),
        "date": (datetime.date.today() + datetime.timedelta(days=day_index)).isoformat(),
        "session": "Upper A",
        "duration": 3600,
        "volume": 20000,
        "rpe": 8,
        "notes": "Good session, felt strong. " * 5, # Some notes
        "exercises": exercises
    }
    return entry

def simulate_growth():
    logs = []

    # 3 sessions per week = ~156 sessions per year
    sessions_per_year = 156
    years_to_simulate = 10

    print(f"--- Simulating {sessions_per_year} sessions/year ---")

    limit_bytes = 5 * 1024 * 1024 # 5MB

    for year in range(1, years_to_simulate + 1):
        for i in range(sessions_per_year):
            logs.append(generate_log_entry(len(logs)))

        # Serialize to measure size
        data = json.dumps(logs)
        size_bytes = len(data.encode('utf-8'))
        size_mb = size_bytes / (1024 * 1024)

        print(f"Year {year}: {len(logs)} logs | Size: {size_mb:.2f} MB")

        if size_bytes > limit_bytes:
            print(f"!!! CRITICAL: Storage Limit Exceeded in Year {year} !!!")
            estimated_months = (limit_bytes / (size_bytes / (year * 12)))
            print(f"Estimated Time to Failure: {estimated_months:.1f} months")
            return

if __name__ == "__main__":
    simulate_growth()
