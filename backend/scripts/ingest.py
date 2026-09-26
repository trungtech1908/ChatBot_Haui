"""Nạp tài liệu vào Qdrant: PDF -> OCR (Nanonets, chạy GPU) -> chia chunk -> embedding (bge-m3) + BM25 -> Qdrant.

Ghi thẳng vào collection hybrid QDRANT_COLLECTION (xóa rồi tạo lại). Chunk được lưu ra assets/chunks.json
để lần sau chỉ cần dựng lại index mà không phải OCR lại (không cần GPU):

    cd backend
    uv sync --extra gpu --extra ingest && uv run --no-sync python scripts/ingest.py      # OCR + index
    uv sync --extra cpu && uv run --no-sync python scripts/ingest.py --from-chunks       # chỉ index lại từ file

Trước khi OCR, script kiểm tra hết (PDF, ghi file, Qdrant URL/key/quyền ghi, GPU, poppler, tải model); sai là dừng
ngay. Tiến độ OCR được lưu sau từng PDF vào assets/chunks.partial.json: lỗi giữa chừng thì chạy lại lệnh cũ, các
PDF đã OCR được bỏ qua (--fresh để OCR lại từ đầu). Xong hết mới thay vào assets/chunks.json.
"""
import argparse
import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

from qdrant_client import QdrantClient
from tqdm.auto import tqdm

from chatbot_haui.ai.indexing import QdrantCheckError, check_qdrant, make_points, recreate_collection
from chatbot_haui.core.config import settings

CHUNKS_FILE = Path(__file__).resolve().parents[1] / "assets" / "chunks.json"
# Tiến độ OCR dở dang: tách khỏi chunks.json (file đã commit) để lần chạy lỗi không ghi đè bản đầy đủ
PARTIAL_FILE = CHUNKS_FILE.with_name("chunks.partial.json")
OCR_MODEL = "nanonets/Nanonets-OCR2-3B"
MAX_ITEMS_PER_CHUNK = 6
UPSERT_BATCH = 256

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
        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor

        self.model = AutoModelForImageTextToText.from_pretrained(
            OCR_MODEL, torch_dtype=torch.float16, device_map="auto"
        ).eval()
        self.processor = AutoProcessor.from_pretrained(OCR_MODEL)

    def image_to_markdown(self, image, max_new_tokens: int = 2048) -> str:
        import torch

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
        import torch
        from pdf2image import convert_from_path

        # Mỗi trang: OCR, bỏ tag số trang/watermark, nối cách 1 dòng trống; bar: thanh tiến trình chung (theo trang)
        pages = []
        for page in convert_from_path(pdf_path, dpi=200):
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


# ================== Kiểm tra trước khi chạy ==================
def fail(message: str):
    raise SystemExit("❌ " + message)


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        fail(f"{path} không phải JSON hợp lệ")
    if not isinstance(data, dict):
        fail(f"{path} phải là object {{tên_văn_bản: [chunk, ...]}}")
    return data


def preflight(from_chunks: Path | None, fresh: bool) -> tuple[list[Path], dict, QdrantClient]:
    """Kiểm tra mọi thứ TRƯỚC khi OCR / embedding. Trả về (PDF cần xử lý, chunk đã có, client Qdrant)."""
    print("=== Kiểm tra trước khi chạy ===")
    pdfs: list[Path] = []
    done: dict = {}
    if from_chunks:
        if not from_chunks.is_file():
            fail(f"Không thấy file chunk {from_chunks}")
        done = load_json(from_chunks)
        if not any(done.values()):
            fail(f"{from_chunks} không có chunk nào")
        print(f"✅ File chunk: {from_chunks} ({sum(map(len, done.values()))} chunk, {len(done)} văn bản)")
    else:
        pdfs = sorted(settings.documents_dir.glob("*.pdf"))
        if not pdfs:
            fail(f"Không có PDF trong {settings.documents_dir} (chạy lệnh từ backend/?)")
        print(f"✅ PDF: {len(pdfs)} file trong {settings.documents_dir}")
        try:
            probe = CHUNKS_FILE.parent / ".kiem_tra_ghi"
            probe.write_text("ok")
            probe.unlink()
        except OSError as e:
            fail(f"Không ghi được vào {CHUNKS_FILE.parent}: {e}")
        if fresh and PARTIAL_FILE.exists():
            PARTIAL_FILE.unlink()
        if PARTIAL_FILE.exists():
            stems = {p.stem for p in pdfs}
            done = {k: v for k, v in load_json(PARTIAL_FILE).items() if k in stems}
        print(f"✅ Lưu tiến độ: {PARTIAL_FILE.name} ({len(done)}/{len(pdfs)} PDF đã OCR ở lần chạy trước, sẽ bỏ qua)")

    if not settings.qdrant_url or not settings.qdrant_api_key:
        fail("Thiếu QDRANT_URL hoặc QDRANT_API_KEY trong cấu hình")
    qdrant = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key, timeout=60)
    try:
        exists = check_qdrant(qdrant, settings.qdrant_collection)
    except QdrantCheckError as e:
        fail(str(e))
    state = "đã có, sẽ bị xóa và nạp lại" if exists else "chưa có, sẽ tạo mới"
    print(f"✅ Qdrant: kết nối được, key có quyền ghi; collection '{settings.qdrant_collection}' {state}")

    todo = [p for p in pdfs if p.stem not in done]
    if todo:
        import torch
        if not torch.cuda.is_available():
            fail("Không thấy GPU CUDA (cần cho OCR). Cài môi trường GPU: uv sync --extra gpu --extra ingest")
        props = torch.cuda.get_device_properties(0)
        vram = props.total_memory / 1024 ** 3
        warn = "  ⚠️ dưới 8 GB, OCR có thể hết bộ nhớ" if vram < 8 else ""
        print(f"✅ GPU: {props.name}, {vram:.0f} GB VRAM{warn}")
        if not shutil.which("pdftoppm"):
            fail("Chưa cài poppler (pdf2image cần): sudo apt install poppler-utils")
        print("✅ poppler: có")

    # Tải trước model: lỗi mạng / Hugging Face lộ ra ngay thay vì sau khi OCR xong
    from huggingface_hub import snapshot_download
    skip = ["onnx/*", "*.onnx", "*.onnx_data", "imgs/*", "flax_model.msgpack", "rust_model.ot", "tf_model.h5"]
    for repo in ([OCR_MODEL] if todo else []) + [settings.embedding_model]:
        try:
            snapshot_download(repo, ignore_patterns=skip)
        except Exception as e:
            fail(f"Không tải được model {repo} ({type(e).__name__}): {str(e)[:150]}")
        print(f"✅ Model {repo}: đã tải")

    print(f"=== Kiểm tra xong: cần OCR {len(todo)}/{len(pdfs)} PDF ===\n" if pdfs else "=== Kiểm tra xong ===\n")
    return todo, done, qdrant


# ================== OCR ==================
def save_json(path: Path, data: dict):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)  # ghi file tạm rồi đổi tên: bị ngắt giữa chừng không hỏng file đã lưu


def ocr_pdfs(todo: list[Path], done: dict) -> dict[str, list[str]]:
    import torch
    from pdf2image import pdfinfo_from_path

    ocr = OCR()
    # Một thanh tiến trình duy nhất, chạy theo tổng số trang của mọi PDF cần OCR
    total_pages = sum(pdfinfo_from_path(str(pdf))["Pages"] for pdf in todo)
    with tqdm(total=total_pages, desc="OCR", unit="trang") as bar:
        for pdf in todo:
            bar.set_postfix_str(pdf.name)
            # source = tên PDF (không đuôi), khớp mã văn bản trong prompts/document_descriptions.json
            done[pdf.stem] = MarkdownChunker(max_items_per_chunk=MAX_ITEMS_PER_CHUNK).chunk(ocr.pdf_to_markdown(pdf, bar))
            save_json(PARTIAL_FILE, done)  # lưu sau TỪNG PDF
    del ocr
    torch.cuda.empty_cache()
    return done


# ================== Qdrant ==================
def index(qdrant: QdrantClient, texts: List[str], sources: List[str]):
    from FlagEmbedding import BGEM3FlagModel

    # Embedding xong hết rồi mới đụng tới collection: lỗi ở bước này không làm mất collection đang có
    embedder = BGEM3FlagModel(settings.embedding_model, use_fp16=False)
    dense = embedder.encode(texts, batch_size=12, max_length=8192)["dense_vecs"]

    collection = settings.qdrant_collection
    recreate_collection(qdrant, collection)  # nạp lại toàn bộ để không còn chunk cũ
    points = make_points(texts, sources, dense)
    for start in range(0, len(points), UPSERT_BATCH):
        qdrant.upsert(collection, points=points[start:start + UPSERT_BATCH])
    print(f"Đã đẩy {len(points)} chunk (dense + BM25) lên '{collection}'")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-chunks", nargs="?", const=CHUNKS_FILE, type=Path, metavar="FILE",
                    help=f"bỏ qua OCR, dựng lại index từ file chunk (mặc định {CHUNKS_FILE.name})")
    ap.add_argument("--fresh", action="store_true", help=f"bỏ tiến độ cũ trong {PARTIAL_FILE.name}, OCR lại mọi PDF")
    args = ap.parse_args()

    todo, chunks_by_doc, qdrant = preflight(args.from_chunks, args.fresh)
    if not args.from_chunks:
        if todo:
            chunks_by_doc = ocr_pdfs(todo, chunks_by_doc)
        save_json(CHUNKS_FILE, chunks_by_doc)  # đủ mọi PDF rồi mới thay bản chính
        PARTIAL_FILE.unlink(missing_ok=True)
        print(f"Đã lưu {sum(map(len, chunks_by_doc.values()))} chunk ra {CHUNKS_FILE}")

    texts = [c for doc in chunks_by_doc.values() for c in doc]
    sources = [name for name, doc in chunks_by_doc.items() for _ in doc]
    try:
        index(qdrant, texts, sources)
    except Exception as e:
        fail(f"Lỗi khi embedding / đẩy lên Qdrant ({type(e).__name__}): {str(e)[:200]}\n"
             f"Chunk đã lưu ở {CHUNKS_FILE}: sửa lỗi rồi chạy scripts/ingest.py --from-chunks, không cần OCR lại.")


if __name__ == "__main__":
    main()
