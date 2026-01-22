import re
from typing import List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class Section:
    number: str
    level: int           # 1 = IN HOA, 2 = in đậm thường
    title: str
    content: List[str] = field(default_factory=list)
    children: List['Section'] = field(default_factory=list)


class MarkdownChunker:
    def __init__(self, max_items_per_chunk: int = 3):
        self.max_items = max_items_per_chunk
        self.flat_sections = []
        self.root_sections = []

    def is_uppercase_heading(self, line: str) -> bool:
        clean = re.sub(r'\*\*(.+?)\*\*', r'\1', line).strip()
        if not clean:
            return False
        letters = re.findall(r'[a-zA-ZÀ-ỹ]', clean)
        if not letters:
            return False
        uppercase_count = sum(1 for c in letters if c.isupper() or ord(c) > 127)
        return uppercase_count / len(letters) >= 0.8

    def is_bold_lowercase_heading(self, line: str) -> bool:
        if not re.match(r'\*\*(.+?)\*\*', line):
            return False
        match = re.search(r'\*\*(.+?)\*\*', line)
        if not match:
            return False
        text = match.group(1).strip()
        letters = re.findall(r'[a-zA-ZÀ-ỹ]', text)
        if not letters:
            return False
        lowercase_count = sum(
            1 for c in letters if c.islower() or (ord(c) > 127 and c.lower() == c)
        )
        return lowercase_count / len(letters) >= 0.5

    def parse_markdown(self, filepath: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        current_section = None
        current_content = []
        level1_counter = 0
        level2_counter = 0
        bold_merge_count = 0   # <<< CHỈ THÊM BIẾN NÀY

        for line in lines:
            line = line.rstrip()

            if not line.strip():
                if current_section:
                    current_content.append(line)
                continue

            # ===== LEVEL 1 =====
            if self.is_uppercase_heading(line):
                title = re.sub(r'\*\*(.+?)\*\*', r'\1', line).strip()

                if current_section and current_section.level == 1:
                    current_section.title += " – " + title
                    continue

                if current_section:
                    current_section.content = current_content
                    self.flat_sections.append(current_section)

                level1_counter += 1
                level2_counter = 0
                bold_merge_count = 0   # RESET

                current_section = Section(
                    number=str(level1_counter),
                    level=1,
                    title=title,
                    content=[]
                )
                current_content = []
                continue

            # ===== LEVEL 2 =====
            if self.is_bold_lowercase_heading(line):
                title = re.sub(r'\*\*(.+?)\*\*', r'\1', line).strip()

                # >>> GỘP TỐI ĐA 3 LẦN <<<
                if current_section and current_section.level == 2 and bold_merge_count < 3:
                    current_section.title += " – " + title
                    bold_merge_count += 1
                    continue

                if current_section:
                    current_section.content = current_content
                    self.flat_sections.append(current_section)

                level2_counter += 1
                bold_merge_count = 1   # bắt đầu chuỗi mới

                current_section = Section(
                    number=f"{level1_counter}.{level2_counter}",
                    level=2,
                    title=title,
                    content=[]
                )
                current_content = []
                continue

            # ===== CONTENT =====
            bold_merge_count = 0
            if current_section:
                current_content.append(line)

        if current_section:
            current_section.content = current_content
            self.flat_sections.append(current_section)

        self._build_hierarchy()

    def _build_hierarchy(self):
        stack = []
        for sec in self.flat_sections:
            while stack and stack[-1].level >= sec.level:
                stack.pop()
            if stack:
                stack[-1].children.append(sec)
            else:
                self.root_sections.append(sec)
            stack.append(sec)

    def _find_section(self, section_num: str) -> Optional[Section]:
        for sec in self.flat_sections:
            if sec.number == section_num:
                return sec
        return None

    def _get_level1_subsections(self, parent: Section) -> List[Section]:
        return parent.children

    def _render_section_full(self, sec: Section) -> str:
        if sec.level == 1:
            result = f"**{sec.title.upper()}**\n"
        else:
            result = f"**{sec.title}**\n"

        for line in sec.content:
            result += line + "\n"

        for child in sec.children:
            result += self._render_section_full(child)

        return result

    # ===== CHUNK LOGIC GIỮ NGUYÊN =====

    def find_leaf_items(self, content: List[str]) -> List[Tuple[int, int, str]]:
        items = []
        i = 0
        while i < len(content):
            line = content[i].strip()
            if not line:
                i += 1
                continue

            if re.match(r'^\d+\.\s+', line):
                start = i
                i += 1
                while i < len(content):
                    next_line = content[i].strip()
                    if (re.match(r'^\d+\.\s+', next_line)
                        or re.match(r'^[a-z]\)\s+', next_line)
                        or self.is_uppercase_heading(next_line)
                        or self.is_bold_lowercase_heading(next_line)):
                        break
                    i += 1
                items.append((start, i - 1, 'numbered'))

            elif re.match(r'^[a-z]\)\s+', line):
                start = i
                i += 1
                while i < len(content):
                    next_line = content[i].strip()
                    if (re.match(r'^\d+\.\s+', next_line)
                        or re.match(r'^[a-z]\)\s+', next_line)
                        or self.is_uppercase_heading(next_line)
                        or self.is_bold_lowercase_heading(next_line)):
                        break
                    i += 1
                items.append((start, i - 1, 'lettered'))
            else:
                i += 1
        return items

    def chunk_section(self, section_num: str) -> List[str]:
        root = self._find_section(section_num)
        if not root:
            return []

        subsections = self._get_level1_subsections(root)
        if not subsections:
            return [self._render_section_full(root)]

        for sub in subsections:
            items = self.find_leaf_items(sub.content)
            if len(items) > self.max_items:
                return self._chunk_by_leaf_items(root, subsections, sub, items)

        return self._chunk_by_subsections(root, subsections)

    def _chunk_by_subsections(self, root, subsections):
        chunks = []
        n = (len(subsections) + self.max_items - 1) // self.max_items
        for i in range(n):
            result = f"**{root.title.upper()}**\n"
            for line in root.content:
                result += line + "\n"
            for sub in subsections[i*self.max_items:(i+1)*self.max_items]:
                result += self._render_section_full(sub)
            chunks.append(result)
        return chunks

    def _chunk_by_leaf_items(self, root, all_subsections, target, leaf_items):
        chunks = []
        n = (len(leaf_items) + self.max_items - 1) // self.max_items
        for i in range(n):
            result = f"**{root.title.upper()}**\n"
            for line in root.content:
                result += line + "\n"
            start = i * self.max_items
            end = min(start + self.max_items, len(leaf_items))
            for sub in all_subsections:
                result += f"**{sub.title}**\n"
                if sub.number == target.number:
                    s = leaf_items[start:end][0][0]
                    e = leaf_items[start:end][-1][1]
                    for j in range(s, e + 1):
                        result += sub.content[j] + "\n"
                else:
                    for line in sub.content:
                        result += line + "\n"
            chunks.append(result)
        return chunks

    def chunk_all_documents(self, input_file: str, output_file: str):
        self.parse_markdown(input_file)
        with open(output_file, 'w', encoding='utf-8') as f:
            for root in self.root_sections:
                for i, chunk in enumerate(self.chunk_section(root.number), 1):
                    f.write(f"===== CHUNK {i} =====\n")
                    f.write(chunk + "\n")


if __name__ == "__main__":
    chunker = MarkdownChunker(max_items_per_chunk=3)
    chunker.chunk_all_documents("ChinhSachSV.md", "output.txt")
    print("✓ Đã chunk xong, kết quả ở output.txt")
