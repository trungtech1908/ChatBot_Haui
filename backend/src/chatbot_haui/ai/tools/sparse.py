"""Vector sparse kiểu BM25 cho tìm kiếm hybrid trên Qdrant.

Token = unigram + bigram âm tiết (chữ thường, NFC, bỏ thẻ HTML). Bigram giữ các cụm nhiều âm tiết
("học kỳ phụ" → "học_kỳ", "kỳ_phụ") mà không cần bộ tách từ tiếng Việt.
Trọng số tài liệu = phần TF của BM25; IDF do Qdrant tính phía server (Modifier.IDF), nên
query chỉ cần đánh dấu token có mặt.
"""
import re
import unicodedata
import zlib
from collections import Counter

K1, B = 1.2, 0.75
_TAG = re.compile(r"<[^>]+>")
_WORD = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", _TAG.sub(" ", text).lower())
    words = _WORD.findall(text)
    return words + [f"{a}_{b}" for a, b in zip(words, words[1:])]


def _index(token: str) -> int:
    # crc32 ổn định giữa các tiến trình (hash() của Python thì không); va chạm hiếm, chấp nhận được
    return zlib.crc32(token.encode())


def _to_sparse(weights: dict[int, float]) -> tuple[list[int], list[float]]:
    items = sorted(weights.items())
    return [i for i, _ in items], [w for _, w in items]


def encode_document(text: str, avg_len: float) -> tuple[list[int], list[float]]:
    tokens = tokenize(text)
    norm = K1 * (1 - B + B * len(tokens) / avg_len)
    weights: dict[int, float] = {}
    for tok, tf in Counter(tokens).items():
        idx = _index(tok)
        weights[idx] = weights.get(idx, 0.0) + tf * (K1 + 1) / (tf + norm)
    return _to_sparse(weights)


def encode_query(text: str) -> tuple[list[int], list[float]]:
    return _to_sparse({_index(tok): 1.0 for tok in set(tokenize(text))})


def average_length(texts: list[str]) -> float:
    return sum(len(tokenize(t)) for t in texts) / max(len(texts), 1)
