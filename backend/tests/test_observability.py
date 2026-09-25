from chatbot_haui.ai.observability import mask


def test_mask_strings_and_sensitive_keys():
    data = {
        "input": "SV 2024619567 hỏi, email lan.nt@gmail.com, sđt 0912345678, nợ 9541800 đồng",
        "profile": {"ho_ten": "Nguyễn Văn A", "ma_sv": "2024619567", "nganh": "Công nghệ thông tin"},
        "rows": [{"so_tien": 700000, "ho_ten": "B"}],
    }
    out = mask(data=data)
    assert "2024619567" not in str(out) and "gmail" not in str(out) and "0912345678" not in str(out)
    assert "Nguyễn Văn A" not in str(out) and out["profile"]["nganh"] == "Công nghệ thông tin"
    # Số liệu cần để debug được giữ
    assert "9541800" in out["input"] and out["rows"][0]["so_tien"] == 700000
