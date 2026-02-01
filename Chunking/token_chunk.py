import os
import json
from transformers import AutoTokenizer

ROOT_DIR = "chunks"

tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-m3")

global_max_tokens = 0
global_max_info = None

for entry in os.scandir(ROOT_DIR):
    if not entry.is_dir():
        continue

    # tìm file json duy nhất trong thư mục con
    json_files = [
        f for f in os.listdir(entry.path)
        if f.lower().endswith(".json")
    ]

    if len(json_files) != 1:
        continue

    json_path = os.path.join(entry.path, json_files[0])

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        for text in item.get("subchunks", []):
            token_count = len(
                tokenizer.encode(text, add_special_tokens=False)
            )

            if token_count > global_max_tokens:
                global_max_tokens = token_count
                global_max_info = {
                    "folder": entry.name,
                    "file": json_files[0],
                    "level1": item.get("level1"),
                    "token_count": token_count
                }

print("Số token lớn nhất:", global_max_tokens)
print("Thông tin tương ứng:", global_max_info)
