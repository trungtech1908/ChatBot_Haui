import os
import re

ROOT_DIR = "../PreProcess/Md"
OUTPUT_NAME = "merged.md"

page_pattern = re.compile(r"page_(\d+)\.md$")
remove_tag_pattern = re.compile(
    r"<page_number>.*?</page_number>|<watermark>.*?</watermark>",
    re.DOTALL
)

for entry in os.scandir(ROOT_DIR):
    if not entry.is_dir():
        continue

    md_files = []

    for name in os.listdir(entry.path):
        match = page_pattern.match(name)
        if match:
            page_num = int(match.group(1))
            md_files.append((page_num, os.path.join(entry.path, name)))

    if not md_files:
        continue

    md_files.sort(key=lambda x: x[0])

    output_path = os.path.join(entry.path, OUTPUT_NAME)

    with open(output_path, "w", encoding="utf-8") as out:
        for _, file_path in md_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            content = remove_tag_pattern.sub("", content)
            out.write(content.strip() + "\n\n")

    print(f"Đã gộp {len(md_files)} file trong {entry.name}")
