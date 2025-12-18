import os
import json

DIR_PATH = "Validation_JUDGE"

pass_count = 0
total = 0

for filename in os.listdir(DIR_PATH):
    if not filename.endswith(".json"):
        continue

    file_path = os.path.join(DIR_PATH, filename)

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        total += 1
        if item.get("judge", {}).get("final_verdict") == "pass":
            pass_count += 1

print(f"PASS: {pass_count}")
print(f"TOTAL: {total}")
print(f"PASS RATE: {pass_count / total if total else 0:.2f}")
