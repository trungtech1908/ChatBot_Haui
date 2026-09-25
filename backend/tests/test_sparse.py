from chatbot_haui.ai.tools.sparse import encode_document, encode_query, tokenize


def test_tokenize_keeps_multi_syllable_terms_as_bigrams():
    tokens = tokenize("Học kỳ phụ <td>Điều 12</td>")
    assert {"học", "kỳ", "phụ", "học_kỳ", "kỳ_phụ", "điều_12"} <= set(tokens)
    assert "td" not in tokens  # thẻ HTML bị bỏ


def test_indices_stable_and_query_matches_document():
    q_idx, _ = encode_query("học kỳ phụ")
    d_idx, d_val = encode_document("Quy định về học kỳ phụ trong năm học", avg_len=10)
    assert q_idx == encode_query("học kỳ phụ")[0]
    assert set(q_idx) <= set(d_idx) and all(v > 0 for v in d_val)


def test_colab_copy_matches_backend_encoder():
    # ingest_colab.py chạy độc lập nên chép bộ mã hóa; hai bản lệch nhau → vector BM25 không khớp khi truy vấn
    import re
    from pathlib import Path

    from chatbot_haui.ai.tools import sparse

    source = (Path(__file__).parents[1] / "scripts" / "ingest_colab.py").read_text(encoding="utf-8")
    block = re.search(r"# BEGIN SPARSE\n(.*?)# END SPARSE", source, re.S).group(1)
    colab: dict = {}
    exec("import re, unicodedata, zlib\nfrom collections import Counter\n" + block, colab)
    texts = ["Điều 7. Học bổng khuyến khích học tập <td>15 tín chỉ</td>", "học kỳ phụ, học lại, cải thiện điểm"]
    avg = sparse.average_length(texts)
    assert colab["average_length"](texts) == avg
    for t in texts:
        assert colab["encode_document"](t, avg) == sparse.encode_document(t, avg)
