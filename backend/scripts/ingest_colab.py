# =====================================================================
# Nạp tài liệu lên Qdrant trên Google Colab (bản chạy độc lập)
# PDF -> OCR (Nanonets) -> chia chunk -> embedding (bge-m3) + BM25 -> Qdrant (collection hybrid)
#
# Cách dùng:
#   1. Runtime > Change runtime type > chọn GPU (T4 trở lên)
#   2. Upload PDF vào PDF_DIR (hoặc để PDF trên Google Drive, bật MOUNT_DRIVE)
#   3. Điền cấu hình bên dưới, copy toàn bộ file vào 1 cell và chạy
#
# Luật chia chunk giống hệt backend/scripts/ingest.py (bản chạy trên máy); bộ mã hóa BM25 giống hệt
# backend/src/chatbot_haui/ai/tools/sparse.py (test tests/test_sparse.py kiểm tra). Sửa thì sửa cả hai nơi.
# Tải file chunks.json về, chép vào backend/assets/ để lần sau index lại không cần OCR:
#   uv run --no-sync python scripts/ingest.py --from-chunks
# =====================================================================

# ============================ CẤU HÌNH ===============================
PDF_DIR = "/content/documents"          # thư mục chứa PDF
MOUNT_DRIVE = False                     # True nếu PDF_DIR nằm trên Google Drive (/content/drive/MyDrive/...)

QDRANT_URL = ""                         # để trống thì lấy từ Colab Secrets: QDRANT_URL
QDRANT_API_KEY = ""                     # để trống thì lấy từ Colab Secrets: QDRANT_API_KEY
QDRANT_COLLECTION = "RAG_ChatBot_HAUI"  # phải trùng QDRANT_COLLECTION của backend; luôn xóa rồi nạp lại toàn bộ

OCR_MODEL = "nanonets/Nanonets-OCR2-3B"
OCR_DPI = 200
OCR_MAX_NEW_TOKENS = 2048
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBED_BATCH_SIZE = 12
MAX_ITEMS_PER_CHUNK = 6
VECTOR_SIZE = 1024                      # bge-m3 dense
UPSERT_BATCH = 256

# File lưu chunk, ghi lại sau TỪNG PDF. Nên để trên Google Drive (MOUNT_DRIVE = True): Colab ngắt kết nối
# không mất kết quả OCR. Tải file về chép vào backend/assets/chunks.json.
SAVE_CHUNKS_JSON = "/content/chunks.json"
REUSE_CHUNKS = True                     # True: PDF đã có trong SAVE_CHUNKS_JSON thì bỏ qua OCR
# =====================================================================


# ---------------------- Cài thư viện (chỉ chạy lần đầu) ----------------------
import subprocess
import sys

subprocess.run(["apt-get", "install", "-y", "-qq", "poppler-utils"], check=True, stdout=subprocess.DEVNULL)
subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q", "FlagEmbedding", "qdrant-client", "pdf2image", "accelerate"],
    check=True,
)

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

import torch
from FlagEmbedding import BGEM3FlagModel
from pdf2image import convert_from_path, pdfinfo_from_path
from PIL import Image
import unicodedata
import zlib
from collections import Counter

from qdrant_client import QdrantClient, models
from tqdm.auto import tqdm
from transformers import AutoModelForImageTextToText, AutoProcessor

if MOUNT_DRIVE:
    from google.colab import drive
    drive.mount("/content/drive")


def fail(message: str):
    raise SystemExit("❌ " + message)


def secret(value: str, name: str) -> str:
    """Ưu tiên giá trị điền trong cấu hình, không có thì đọc Colab Secrets. Thiếu cả hai thì dừng ngay."""
    if value and value.strip():
        return value.strip()
    try:
        from google.colab import userdata
        found = userdata.get(name)
    except Exception as e:  # chưa có secret, chưa bật quyền cho notebook, hoặc không chạy trên Colab
        fail(f"Thiếu {name}: điền vào cấu hình đầu file, hoặc thêm vào Colab Secrets và bật quyền cho notebook "
             f"({type(e).__name__})")
    if not found or not found.strip():
        fail(f"{name} trong Colab Secrets đang rỗng")
    return found.strip()


def preflight() -> tuple[list[Path], QdrantClient, dict]:
    """Kiểm tra mọi thứ TRƯỚC khi OCR. OCR chạy hàng chục phút: lỗi cấu hình phải lộ ra ngay từ đầu."""
    print("=== Kiểm tra trước khi chạy ===")

    # 1. PDF
    pdf_dir = Path(PDF_DIR)
    if not pdf_dir.is_dir():
        hint = " (đường dẫn nằm trên Drive nhưng MOUNT_DRIVE = False?)" if "/drive/" in PDF_DIR and not MOUNT_DRIVE else ""
        fail(f"Không thấy thư mục PDF_DIR = {PDF_DIR}{hint}")
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        fail(f"Không có file .pdf nào trong {PDF_DIR}")
    print(f"✅ PDF: {len(pdfs)} file trong {PDF_DIR}")

    # 2. File lưu chunk: ghi được không, có kết quả OCR cũ dùng lại được không
    done = {}
    if not SAVE_CHUNKS_JSON:
        print("⚠️ SAVE_CHUNKS_JSON trống: lỗi ở bất kỳ bước nào sau OCR sẽ phải OCR lại từ đầu")
    else:
        out = Path(SAVE_CHUNKS_JSON)
        if out.suffix != ".json":
            fail(f"SAVE_CHUNKS_JSON phải là đường dẫn tới một file .json, đang là {SAVE_CHUNKS_JSON}")
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
            probe_file = out.parent / ".kiem_tra_ghi"
            probe_file.write_text("ok")
            probe_file.unlink()
        except OSError as e:
            fail(f"Không ghi được vào thư mục {out.parent}: {e}")
        if out.exists():
            try:
                saved = json.loads(out.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                fail(f"{out} đã có nhưng không phải JSON hợp lệ: xóa file đó hoặc đổi SAVE_CHUNKS_JSON")
            stems = {pdf.stem for pdf in pdfs}
            done = {k: v for k, v in saved.items() if k in stems} if REUSE_CHUNKS else {}
        if not str(out).startswith("/content/drive/"):
            print("⚠️ SAVE_CHUNKS_JSON không nằm trên Google Drive: Colab ngắt kết nối là mất file")
        print(f"✅ Lưu chunk: {out} ({len(done)}/{len(pdfs)} PDF đã OCR sẵn, sẽ bỏ qua)")

    # 3. Qdrant: URL đúng, key đúng, key có quyền ghi
    url, key = secret(QDRANT_URL, "QDRANT_URL"), secret(QDRANT_API_KEY, "QDRANT_API_KEY")
    if not url.startswith(("http://", "https://")):
        fail("QDRANT_URL phải bắt đầu bằng https://")
    qdrant = QdrantClient(url=url, api_key=key, timeout=60)
    try:
        existing = [c.name for c in qdrant.get_collections().collections]
    except Exception as e:
        text = str(e)
        if any(code in text for code in ("401", "403", "Unauthorized", "Forbidden")):
            fail("QDRANT_API_KEY sai hoặc đã bị thu hồi (Qdrant từ chối)")
        fail(f"Không kết nối được QDRANT_URL ({type(e).__name__}): kiểm tra URL và cluster còn chạy không")
    probe = "_ingest_kiem_tra_quyen_ghi"
    try:
        if qdrant.collection_exists(probe):
            qdrant.delete_collection(probe)
        qdrant.create_collection(probe, vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE))
        qdrant.delete_collection(probe)
    except Exception as e:
        fail(f"QDRANT_API_KEY đọc được nhưng không có quyền tạo/xóa collection ({type(e).__name__}): cần key có quyền ghi")
    state = "đã có, sẽ bị xóa và nạp lại" if QDRANT_COLLECTION in existing else "chưa có, sẽ tạo mới"
    print(f"✅ Qdrant: kết nối được, key có quyền ghi; collection '{QDRANT_COLLECTION}' {state}")

    # 4. GPU: chỉ cần khi còn PDF phải OCR
    need_ocr = len(pdfs) - len(done)
    if need_ocr:
        if not torch.cuda.is_available():
            fail("Không thấy GPU: Runtime > Change runtime type > chọn GPU (T4 trở lên)")
        props = torch.cuda.get_device_properties(0)
        vram = props.total_memory / 1024 ** 3
        warn = "  ⚠️ dưới 8 GB, OCR có thể hết bộ nhớ" if vram < 8 else ""
        print(f"✅ GPU: {props.name}, {vram:.0f} GB VRAM{warn}")

    # 5. Tải trước model: lỗi mạng / Hugging Face lộ ra ngay thay vì sau khi OCR xong
    from huggingface_hub import snapshot_download
    skip = ["onnx/*", "*.onnx", "*.onnx_data", "imgs/*", "flax_model.msgpack", "rust_model.ot", "tf_model.h5"]
    for repo in ([OCR_MODEL] if need_ocr else []) + [EMBEDDING_MODEL]:
        try:
            snapshot_download(repo, ignore_patterns=skip)
        except Exception as e:
            fail(f"Không tải được model {repo} ({type(e).__name__}): {str(e)[:150]}")
        print(f"✅ Model {repo}: đã tải")

    print(f"=== Kiểm tra xong: cần OCR {need_ocr}/{len(pdfs)} PDF ===\n")
    return pdfs, qdrant, done


OCR_PROMPT = (
    "Extract the text from the above document as if you were reading it naturally. "
    "Return the tables in html format. "
    "Return the equations in LaTeX representation. "
    "If there is an image in the document and image caption is not present, "
    "add a small description of the image inside the <img></img> tag; otherwise, "
    "add the image caption inside <img></img>. "
    "Watermarks should be wrapped in brackets. "
    "Ex: <watermark>OFFICIAL COPY</watermark>. "
    "Page numbers should be wrapped in brackets. "
    "Ex: <page_number>14</page_number> or <page_number>9/22</page_number>. "
    "Prefer using ☐ and ☑ for check boxes."
)
REMOVE_TAGS = re.compile(r"<page_number>.*?</page_number>|<watermark>.*?</watermark>", re.DOTALL)


# ================== OCR ==================
class OCR:
    def __init__(self):
        self.model = AutoModelForImageTextToText.from_pretrained(
            OCR_MODEL, torch_dtype=torch.float16, device_map="auto"
        ).eval()
        self.processor = AutoProcessor.from_pretrained(OCR_MODEL)

    def image_to_markdown(self, image: Image.Image, max_new_tokens: int = OCR_MAX_NEW_TOKENS) -> str:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": [{"type": "image"}, {"type": "text", "text": OCR_PROMPT}]},
        ]
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(
            text=[text], images=[image.convert("RGB")], padding=True, return_tensors="pt"
        ).to(self.model.device)

        with torch.inference_mode():
            output_ids = self.model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)

        gen_ids = output_ids[:, inputs.input_ids.shape[1]:]
        return self.processor.batch_decode(gen_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)[0]

    def pdf_to_markdown(self, pdf_path: Path, bar=None) -> str:
        # Mỗi trang: OCR, bỏ tag số trang/watermark, nối cách 1 dòng trống; bar: thanh tiến trình chung (theo trang)
        pages = []
        for page in convert_from_path(pdf_path, dpi=OCR_DPI):
            pages.append(REMOVE_TAGS.sub("", self.image_to_markdown(page)).strip())
            torch.cuda.empty_cache()
            if bar is not None:
                bar.update(1)
        return "\n\n".join(pages) + "\n\n"


# ================== Chunking (giữ nguyên luật chia) ==================
@dataclass
class Section:
    """Đại diện cho một mục trong tài liệu"""
    number: str
    level: int  # 1 = Level1 (IN HOA), 2 = Level2 (in thường)
    title: str
    content: List[str] = field(default_factory=list)
    children: List['Section'] = field(default_factory=list)


class MarkdownChunker:
    def __init__(self, max_items_per_chunk: int = 3):
        self.max_items = max_items_per_chunk
        self.flat_sections = []
        self.root_sections = []

    def is_bold_uppercase(self, line: str) -> bool:
        """Kiểm tra dòng có phải **IN HOA** không"""
        if not re.match(r'^\*\*(.+?)\*\*\s*$', line):
            return False
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', line).strip()
        if not text:
            return False
        letters = re.findall(r'[a-zA-ZÀ-ỹ]', text)
        if not letters:
            return False
        uppercase_count = sum(1 for c in letters if c.isupper() or ord(c) > 127)
        return uppercase_count / len(letters) >= 0.8

    def is_bold_lowercase(self, line: str) -> bool:
        """Kiểm tra dòng có phải **in thường** không"""
        if not re.match(r'^\*\*(.+?)\*\*', line):
            return False
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', line).strip()
        if not text:
            return False
        letters = re.findall(r'[a-zA-ZÀ-ỹ]', text)
        if not letters:
            return False
        lowercase_count = sum(1 for c in letters if c.islower() or (ord(c) > 127 and c.lower() == c))
        return lowercase_count / len(letters) >= 0.5

    def parse_markdown(self, text: str):
        """Phân tích nội dung Markdown"""
        lines = text.splitlines()

        current_section = None
        current_content = []
        level1_counter = 0
        level2_counter = 0

        # Buffer để gộp các dòng **IN HOA** liền nhau
        uppercase_buffer = []

        i = 0
        while i < len(lines):
            line = lines[i].rstrip()

            # Bỏ qua page_number, watermark, img
            if re.match(r'^<(page_number|watermark|img)>', line):
                i += 1
                continue

            # Kiểm tra **IN HOA**
            if self.is_bold_uppercase(line):
                uppercase_buffer.append(line)
                i += 1
                continue

            # Nếu có buffer và gặp dòng không phải IN HOA → flush buffer
            if uppercase_buffer:
                # Lưu section trước
                if current_section:
                    current_section.content = current_content
                    self.flat_sections.append(current_section)

                level1_counter += 1
                level2_counter = 0

                # Gộp các dòng IN HOA
                combined_title = ' - '.join(
                    re.sub(r'\*\*(.+?)\*\*', r'\1', l).strip()
                    for l in uppercase_buffer
                )

                current_section = Section(str(level1_counter), 1, combined_title, [])
                current_content = []
                uppercase_buffer = []

            # Kiểm tra **in thường**
            if self.is_bold_lowercase(line):
                if current_section:
                    current_section.content = current_content
                    self.flat_sections.append(current_section)

                level2_counter += 1
                title = re.sub(r'\*\*(.+?)\*\*', r'\1', line).strip()
                number = f"{level1_counter}.{level2_counter}"

                current_section = Section(number, 2, title, [])
                current_content = []
                i += 1
                continue

            # Nội dung thường
            if not line.strip():
                if current_section:
                    current_content.append(line)
                i += 1
                continue

            if current_section:
                current_content.append(line)
            i += 1

        # Flush buffer cuối
        if uppercase_buffer:
            if current_section:
                current_section.content = current_content
                self.flat_sections.append(current_section)

            level1_counter += 1
            combined_title = ' - '.join(
                re.sub(r'\*\*(.+?)\*\*', r'\1', l).strip()
                for l in uppercase_buffer
            )
            current_section = Section(str(level1_counter), 1, combined_title, [])
            current_content = []

        # Lưu section cuối
        if current_section:
            current_section.content = current_content
            self.flat_sections.append(current_section)

        self._build_hierarchy()

    def _build_hierarchy(self):
        """Xây dựng cây phân cấp"""
        stack = []
        for sec in self.flat_sections:
            while stack and stack[-1].level >= sec.level:
                stack.pop()
            if stack:
                stack[-1].children.append(sec)
            else:
                self.root_sections.append(sec)
            stack.append(sec)

    def find_leaf_items(self, content: List[str]) -> List[Tuple[int, int, str, int]]:
        """Tìm leaf items với level động: 1., 2. hoặc a), b) hoặc <table>
        Returns: List of (start_line, end_line, item_type, level)
        Level được xác định theo thứ tự xuất hiện (xuất hiện trước = level thấp hơn)
        """
        # Bước 1: Xác định thứ tự xuất hiện của các loại item
        first_occurrence = {}

        for i, line in enumerate(content):
            line_stripped = line.strip()
            if not line_stripped:
                continue

            if '<table' in line_stripped.lower() and 'table' not in first_occurrence:
                first_occurrence['table'] = i
            elif re.match(r'^\d+\.\s+', line_stripped) and 'numbered' not in first_occurrence:
                first_occurrence['numbered'] = i
            elif re.match(r'^[a-z]\)\s+', line_stripped) and 'lettered' not in first_occurrence:
                first_occurrence['lettered'] = i

        # Bước 2: Gán level dựa trên thứ tự xuất hiện
        level_map = {}
        sorted_types = sorted(first_occurrence.items(), key=lambda x: x[1])
        for level, (item_type, _) in enumerate(sorted_types, start=2):  # Level 2 trở đi
            level_map[item_type] = level

        # Bước 3: Parse items với level đã xác định
        items = []
        i = 0

        while i < len(content):
            line = content[i].strip()

            if not line:
                i += 1
                continue

            # Bảng <table>
            if re.match(r'^<table', line, re.IGNORECASE):
                start = i
                i += 1
                while i < len(content):
                    if re.search(r'</table>', content[i], re.IGNORECASE):
                        i += 1
                        break
                    i += 1
                level = level_map.get('table', 2)
                items.append((start, i - 1, 'table', level))
                continue

            # Bullets số: "1.", "2."
            if re.match(r'^\d+\.\s+', line):
                start = i
                current_level = level_map.get('numbered', 2)
                i += 1
                while i < len(content):
                    next_line = content[i].strip()
                    # Kiểm tra item cùng level hoặc level cao hơn
                    is_same_or_higher = False
                    if re.match(r'^\d+\.\s+', next_line):
                        is_same_or_higher = True
                    elif re.match(r'^[a-z]\)\s+', next_line):
                        if level_map.get('lettered', 3) <= current_level:
                            is_same_or_higher = True
                    elif re.match(r'^<table', next_line, re.IGNORECASE):
                        if level_map.get('table', 3) <= current_level:
                            is_same_or_higher = True
                    elif self.is_bold_uppercase(next_line) or self.is_bold_lowercase(next_line):
                        is_same_or_higher = True

                    if is_same_or_higher:
                        break
                    i += 1
                items.append((start, i - 1, 'numbered', current_level))
                continue

            # Bullets chữ: "a)", "b)"
            if re.match(r'^[a-z]\)\s+', line):
                start = i
                current_level = level_map.get('lettered', 2)
                i += 1
                while i < len(content):
                    next_line = content[i].strip()
                    is_same_or_higher = False
                    if re.match(r'^[a-z]\)\s+', next_line):
                        is_same_or_higher = True
                    elif re.match(r'^\d+\.\s+', next_line):
                        if level_map.get('numbered', 3) <= current_level:
                            is_same_or_higher = True
                    elif re.match(r'^<table', next_line, re.IGNORECASE):
                        if level_map.get('table', 3) <= current_level:
                            is_same_or_higher = True
                    elif self.is_bold_uppercase(next_line) or self.is_bold_lowercase(next_line):
                        is_same_or_higher = True

                    if is_same_or_higher:
                        break
                    i += 1
                items.append((start, i - 1, 'lettered', current_level))
                continue

            i += 1

        return items

    def _render_section_full(self, sec: Section) -> str:
        """Render toàn bộ section"""
        if sec.level == 1:
            result = f"{sec.title}\n\n"
        else:
            result = f"**{sec.title}**\n\n"

        for line in sec.content:
            result += line + "\n"

        for child in sec.children:
            result += self._render_section_full(child)

        return result

    def chunk_section(self, root: Section) -> List[str]:
        """Chunk một section thành subchunks"""
        subsections = root.children

        if not subsections:
            return [self._render_section_full(root).strip()]

        # Tìm subsection có leaf items > n
        target_subsection = None
        target_leaf_items = []

        for sub in subsections:
            items = self.find_leaf_items(sub.content)
            if len(items) > self.max_items:
                target_subsection = sub
                target_leaf_items = items
                break

        if target_subsection:
            return self._chunk_by_leaf_items(root, subsections, target_subsection, target_leaf_items)
        else:
            return self._chunk_by_subsections(root, subsections)

    def _chunk_by_subsections(self, root: Section, subsections: List[Section]) -> List[str]:
        """Chunk theo subsections (n subsections/chunk)"""
        chunks = []
        num_chunks = (len(subsections) + self.max_items - 1) // self.max_items

        for chunk_idx in range(num_chunks):
            start_idx = chunk_idx * self.max_items
            end_idx = min(start_idx + self.max_items, len(subsections))

            result = f"{root.title}\n\n"

            for line in root.content:
                result += line + "\n"

            for sub in subsections[start_idx:end_idx]:
                result += self._render_section_full(sub)

            chunks.append(result.strip())

        return chunks

    def _chunk_by_leaf_items(self, root: Section, all_subsections: List[Section],
                             target: Section, leaf_items: List[Tuple[int, int, str, int]]) -> List[str]:
        """Chunk theo leaf items - CHỈ chunk items ở level thấp nhất"""
        # Lọc chỉ lấy items có level thấp nhất (level 2)
        min_level = min(item[3] for item in leaf_items)
        level2_items = [(s, e, t, l) for s, e, t, l in leaf_items if l == min_level]

        # Nếu không có items level 2 hoặc <= n → không chunk
        if len(level2_items) <= self.max_items:
            return [self._render_section_full(root).strip()]

        target_index = next((i for i, s in enumerate(all_subsections) if s.number == target.number), -1)

        context_before = max(0, target_index - (self.max_items - 1) // 2)
        context_after = min(len(all_subsections), target_index + 1 + (self.max_items - 1) // 2)

        total_needed = self.max_items
        actual_range = context_after - context_before

        if actual_range < total_needed:
            if context_before > 0:
                context_before = max(0, context_before - (total_needed - actual_range))
            elif context_after < len(all_subsections):
                context_after = min(len(all_subsections), context_after + (total_needed - actual_range))

        context_subsections = all_subsections[context_before:context_after]

        chunks = []
        num_chunks = (len(level2_items) + self.max_items - 1) // self.max_items

        for chunk_idx in range(num_chunks):
            start_idx = chunk_idx * self.max_items
            end_idx = min(start_idx + self.max_items, len(level2_items))

            result = f"{root.title}\n\n"

            for line in root.content:
                result += line + "\n"

            for sub in context_subsections:
                result += f"**{sub.title}**\n\n"

                if sub.number == target.number:
                    selected_items = level2_items[start_idx:end_idx]
                    if selected_items:
                        first_start = selected_items[0][0]
                        last_end = selected_items[-1][1]
                        for i in range(first_start, last_end + 1):
                            if i < len(sub.content):
                                result += sub.content[i] + "\n"

                    for child in sub.children:
                        result += self._render_section_full(child)
                else:
                    for line in sub.content:
                        result += line + "\n"
                    for child in sub.children:
                        result += self._render_section_full(child)

            chunks.append(result.strip())

        return chunks

    def chunk(self, text: str) -> List[str]:
        """Chia toàn bộ document thành danh sách subchunk"""
        self.parse_markdown(text)
        return [sub for root in self.root_sections for sub in self.chunk_section(root)]


# ================== BM25 (chép từ chatbot_haui/ai/tools/sparse.py) ==================
# BEGIN SPARSE
K1, B = 1.2, 0.75
_TAG = re.compile(r"<[^>]+>")
_WORD = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", _TAG.sub(" ", text).lower())
    words = _WORD.findall(text)
    return words + [f"{a}_{b}" for a, b in zip(words, words[1:])]


def _index(token: str) -> int:
    return zlib.crc32(token.encode())


def encode_document(text: str, avg_len: float) -> tuple[list[int], list[float]]:
    tokens = tokenize(text)
    norm = K1 * (1 - B + B * len(tokens) / avg_len)
    weights: dict[int, float] = {}
    for tok, tf in Counter(tokens).items():
        idx = _index(tok)
        weights[idx] = weights.get(idx, 0.0) + tf * (K1 + 1) / (tf + norm)
    items = sorted(weights.items())
    return [i for i, _ in items], [w for _, w in items]


def average_length(texts: list[str]) -> float:
    return sum(len(tokenize(t)) for t in texts) / max(len(texts), 1)
# END SPARSE


# ================== Qdrant (cấu trúc giống chatbot_haui/ai/indexing.py) ==================
def upsert(qdrant: QdrantClient, texts: List[str], sources: List[str]):
    # Embedding xong hết rồi mới đụng tới collection: lỗi ở bước embedding không làm mất collection đang có
    embedder = BGEM3FlagModel(EMBEDDING_MODEL, use_fp16=True)
    vectors = embedder.encode(texts, batch_size=EMBED_BATCH_SIZE, max_length=8192)["dense_vecs"]

    if qdrant.collection_exists(QDRANT_COLLECTION):
        qdrant.delete_collection(QDRANT_COLLECTION)
    qdrant.create_collection(
        QDRANT_COLLECTION,
        vectors_config={"dense": models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE)},
        sparse_vectors_config={"bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)},
    )
    qdrant.create_payload_index(QDRANT_COLLECTION, field_name="source", field_schema="keyword")

    avg_len = average_length(texts)
    points = []
    for i, (vec, text, src) in enumerate(zip(vectors, texts, sources)):
        indices, values = encode_document(text, avg_len)
        points.append(models.PointStruct(
            id=i,
            vector={"dense": vec.tolist(), "bm25": models.SparseVector(indices=indices, values=values)},
            payload={"source": src, "raw_text": text},
        ))
    for start in range(0, len(points), UPSERT_BATCH):
        qdrant.upsert(QDRANT_COLLECTION, points=points[start:start + UPSERT_BATCH])
    print(f"Đã đẩy {len(points)} chunk (dense + BM25) lên '{QDRANT_COLLECTION}'")


def save_chunks(chunks_by_pdf: dict):
    if not SAVE_CHUNKS_JSON:
        return
    out = Path(SAVE_CHUNKS_JSON)
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(json.dumps(chunks_by_pdf, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(out)  # ghi file tạm rồi đổi tên: bị ngắt giữa chừng cũng không hỏng file đã lưu


def main():
    pdfs, qdrant, chunks_by_pdf = preflight()

    todo = [pdf for pdf in pdfs if pdf.stem not in chunks_by_pdf]
    if todo:
        ocr = OCR()
        # Một thanh tiến trình duy nhất, chạy theo tổng số trang của mọi PDF cần OCR
        total_pages = sum(pdfinfo_from_path(str(pdf))["Pages"] for pdf in todo)
        with tqdm(total=total_pages, desc="OCR", unit="trang") as bar:
            for pdf in todo:
                bar.set_postfix_str(pdf.name)
                # source = tên PDF (không đuôi), khớp mã văn bản trong document_descriptions.json của backend
                chunks_by_pdf[pdf.stem] = MarkdownChunker(max_items_per_chunk=MAX_ITEMS_PER_CHUNK).chunk(
                    ocr.pdf_to_markdown(pdf, bar))
                save_chunks(chunks_by_pdf)  # lưu sau TỪNG PDF: lỗi / ngắt kết nối thì chạy lại cell sẽ bỏ qua phần đã xong
        # Giải phóng GPU của model OCR trước khi embedding
        del ocr
        torch.cuda.empty_cache()

    texts = [c for pdf in pdfs for c in chunks_by_pdf[pdf.stem]]
    sources = [pdf.stem for pdf in pdfs for _ in chunks_by_pdf[pdf.stem]]
    if not texts:
        fail("OCR xong nhưng không ra chunk nào: kiểm tra nội dung PDF")
    print(f"Tổng: {len(texts)} chunk từ {len(pdfs)} PDF")
    try:
        upsert(qdrant, texts, sources)
    except Exception as e:
        kept = (f"\nChunk đã lưu ở {SAVE_CHUNKS_JSON}: sửa lỗi rồi chạy lại cell, phần OCR sẽ được bỏ qua."
                if SAVE_CHUNKS_JSON else "")
        fail(f"Lỗi khi embedding / đẩy lên Qdrant ({type(e).__name__}): {str(e)[:200]}{kept}")

main()
