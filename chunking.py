import os
import re
import json

def chunk_markdown(file_path, output_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    all_chunks = []
    current_level1 = None
    pending_level1 = []
    current_level2 = None
    level2_intro = ""
    current_subchunks = []

    uppercase_vn = "A-ZÀ-Ỹ"
    lowercase_vn = "a-zà-ỹ"

    waiting_for_level2_intro = False

    def flush_current():
        nonlocal current_level1, current_subchunks
        if current_level1 and current_subchunks:
            all_chunks.append({
                "level1": current_level1,
                "subchunks": current_subchunks
            })
        current_subchunks = []

    def finalize_level1():
        nonlocal pending_level1, current_level1
        if pending_level1:
            current_level1 = " ".join(pending_level1)
            pending_level1 = []

    def is_table_line(line):
        return line.startswith("|") and line.endswith("|")

    i = 0
    while i < len(lines):
        line = lines[i]

        # Cấp 1
        if re.fullmatch(rf"\*\*[{uppercase_vn}0-9\s,.\-]+\*\*", line):
            text = re.sub(r"\*\*(.*?)\*\*", r"\1", line).strip()
            pending_level1.append(text)
            i += 1
            continue

        if pending_level1:
            flush_current()
            finalize_level1()

        # Cấp 2
        if re.fullmatch(rf"\*\*[{uppercase_vn}{lowercase_vn}0-9\s,.\-]+\*\*", line):
            text = re.sub(r"\*\*(.*?)\*\*", r"\1", line).strip()
            if not text.isupper():
                current_level2 = text
                level2_intro = ""
                waiting_for_level2_intro = True
            i += 1
            continue

        # Dòng mô tả sau cấp 2
        if waiting_for_level2_intro:
            level2_intro = line
            waiting_for_level2_intro = False
            i += 1
            continue

        # Các mục liệt kê
        if re.match(r"^\d+\.", line) or re.match(r"^[a-zA-Z]\)", line) or re.match(r"^[-•]", line):
            prefix = " ".join(filter(None, [current_level1, current_level2, level2_intro]))
            current_subchunks.append(f"{prefix} {line}".strip())
            i += 1
            continue

        # Bảng dữ liệu
        if is_table_line(line):
            table_block = [line]
            j = i + 1
            while j < len(lines) and is_table_line(lines[j]):
                table_block.append(lines[j])
                j += 1
            table_text = "\n".join(table_block)
            prefix = " ".join(filter(None, [current_level1, current_level2, level2_intro]))
            current_subchunks.append(f"{prefix}\n{table_text}")
            i = j
            continue

        # Nội dung khác
        if current_level2:
            prefix = " ".join(filter(None, [current_level1, current_level2, level2_intro]))
            current_subchunks.append(f"{prefix} {line}".strip())

        i += 1

    if pending_level1:
        flush_current()
        finalize_level1()

    flush_current()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"✅ {os.path.basename(file_path)} → {len(all_chunks)} chunks, lưu vào '{output_path}'")


# --- Xử lý toàn bộ thư mục chứa .md ---
def process_folder(input_folder, output_folder="chunks_json"):
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.endswith(".md"):
            input_path = os.path.join(input_folder, filename)
            output_name = os.path.splitext(filename)[0] + ".json"
            output_path = os.path.join(output_folder, output_name)
            chunk_markdown(input_path, output_path)

    print("\n🎯 Hoàn tất xử lý toàn bộ file .md.")


# Ví dụ chạy
process_folder("output_md_Gemini")
