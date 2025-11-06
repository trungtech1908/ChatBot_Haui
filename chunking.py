import re
import json

def chunk_markdown(file_path, output_path="chunks.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    all_chunks = []
    current_level1 = None
    pending_level1 = []  # lưu tạm nhiều dòng cấp 1 liên tiếp
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
        """Khi đã gom xong các cấp 1 liên tiếp, hợp chúng lại"""
        nonlocal pending_level1, current_level1
        if pending_level1:
            current_level1 = " ".join(pending_level1)
            pending_level1 = []

    def is_table_line(line):
        return line.startswith("|") and line.endswith("|")

    i = 0
    while i < len(lines):
        line = lines[i]

        # --- Nếu là cấp 1 (in hoa toàn bộ) ---
        if re.fullmatch(rf"\*\*[{uppercase_vn}0-9\s,.\-]+\*\*", line):
            text = re.sub(r"\*\*(.*?)\*\*", r"\1", line).strip()
            pending_level1.append(text)
            i += 1
            continue  # đợi xem dòng sau có phải tiếp tục cấp 1 không

        # --- Nếu dòng này KHÔNG phải cấp 1, mà có pending ---
        if pending_level1:
            flush_current()
            finalize_level1()

        # --- Cấp 2: **Chữ đậm thường (chữ thường có dấu)**
        if re.fullmatch(rf"\*\*[{uppercase_vn}{lowercase_vn}0-9\s,.\-]+\*\*", line):
            text = re.sub(r"\*\*(.*?)\*\*", r"\1", line).strip()
            if not text.isupper():
                current_level2 = text
                level2_intro = ""
                waiting_for_level2_intro = True
            i += 1
            continue

        # --- Dòng mô tả ngay sau cấp 2 ---
        if waiting_for_level2_intro:
            level2_intro = line
            waiting_for_level2_intro = False
            i += 1
            continue

        # --- Các mục như 1., a), - ... ---
        if re.match(r"^\d+\.", line) or re.match(r"^[a-zA-Z]\)", line) or re.match(r"^[-•]", line):
            prefix = " ".join(filter(None, [current_level1, current_level2, level2_intro]))
            current_subchunks.append(f"{prefix} {line}".strip())
            i += 1
            continue

        # --- Bảng dữ liệu (cấp 3) ---
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

        # --- Nội dung khác ---
        if current_level2:
            prefix = " ".join(filter(None, [current_level1, current_level2, level2_intro]))
            current_subchunks.append(f"{prefix} {line}".strip())

        i += 1

    # Cuối file mà vẫn còn cấp 1 đang pending
    if pending_level1:
        flush_current()
        finalize_level1()

    flush_current()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"✅ Đã chia {len(all_chunks)} chunk lớn, lưu vào '{output_path}'")


# Ví dụ chạy thử
chunk_markdown("output_md_Gemini/ChinhSachSV.md", "chunks.json")
