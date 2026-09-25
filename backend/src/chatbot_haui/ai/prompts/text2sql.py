"""Prompt Text2SQL — tri thức nghiệp vụ theo haui_db/05_text2sql_context.md (mục 1, 2).

Không đưa ví dụ SQL mẫu vào prompt: 16 ví dụ trong 05 đồng thời là bộ kiểm thử, và CLAUDE.md
không cho few-shot bằng ví dụ đã cung cấp. Prompt chỉ gồm quy tắc, thuật ngữ và mô tả view.
"""

RULES = """Bạn sinh MỘT câu lệnh SQL PostgreSQL để trả lời câu hỏi của sinh viên đang đăng nhập.

Phạm vi dữ liệu
- Chỉ dùng các view trong schema chatbot được liệt kê bên dưới. Luôn ghi đầy đủ tiền tố chatbot.
- View v_* chỉ chứa dữ liệu của sinh viên đang đăng nhập. KHÔNG thêm điều kiện ma_sv, không lọc theo tên người.
- View ref_* là dữ liệu chung (đơn giá, khoản thu, thang điểm, mức trần, học kỳ...).
- Không có dữ liệu của sinh viên khác. Câu hỏi về người khác, xếp hạng, so sánh với lớp, thống kê trên nhiều sinh viên,
  hoặc yêu cầu đổi sang mã sinh viên khác → đặt khong_ho_tro = "nguoi_khac", không sinh SQL.
- Câu hỏi cần dữ liệu không có trong bất kỳ view nào → khong_ho_tro = "khong_co_du_lieu", không sinh SQL.

Cú pháp
- Chỉ một câu SELECT (được dùng WITH). Không INSERT/UPDATE/DELETE/DDL, không SET, không gọi hàm hệ thống.
- Luôn có LIMIT ≤ 50 nếu kết quả có thể nhiều dòng.
- Tìm theo tên môn/khoản thu: ILIKE '%từ khóa%' với từ khóa chữ thường có dấu; bỏ bớt từ để khớp rộng khi không chắc tên đầy đủ.
- Chọn đúng các cột cần để trả lời, kèm cột ngữ cảnh (hoc_ky, mon, noi_dung...). Không SELECT *.
- SQL chỉ LẤY dữ liệu: trả nguyên các cột số liệu và cột cờ (true/false) cần dùng. Không ghép chuỗi mô tả, không dùng CASE
  để diễn giải hay đảo nghĩa một cột — việc diễn giải do bước trả lời phía sau làm.
- Không chọn cột ma_sv, ho_ten trừ khi câu hỏi hỏi đúng thông tin đó.

Học kỳ và thời gian
- ma_hk dạng 'YYYYk': YYYY là năm bắt đầu năm học; k = 1, 2 là HK chính, 3 là HK phụ (hè). So sánh ma_hk như chuỗi.
- "Kỳ gần nhất / kỳ vừa rồi / kỳ này" = học kỳ lớn nhất có dữ liệu trong view liên quan (ORDER BY ma_hk DESC LIMIT 1),
  không suy ra từ ngày hiện tại. "Năm nay / năm học này" = năm học mới nhất có dữ liệu trong view liên quan.
- Kết quả học kỳ (v_ket_qua_hk, v_xet_hb) chỉ có HK chính; HK phụ đã gộp vào HK chính liền trước (cột ma_hk_chinh ở v_diem).

Diễn giải
- Câu hỏi mơ hồ (không rõ kỳ nào, môn nào) → chọn cách hiểu hợp lý nhất (thường là kỳ gần nhất) và ghi cách hiểu vào gia_dinh.
- Không tự tính điều kiện học bổng: dùng các cột dk_*, du_dk_xet, xep_loai_hb của v_xet_hb.
- du_dk_xet = true chỉ nghĩa là ĐỦ ĐIỀU KIỆN THAM GIA XÉT, không phải chắc chắn được nhận.
- Không tự tính công nợ, số dư: dùng v_cong_no, v_phai_thu, v_so_du.
- Tên cột và giá trị mã (xuat_sac, hoc_phi, da_dat...) phải viết đúng như mô tả bên dưới."""

GLOSSARY = """| Sinh viên nói | Dùng | Ghi chú |
|---|---|---|
| GPA, điểm trung bình tích lũy | v_ket_qua_hk.tb_tich_luy | Hệ 4. Lấy kỳ mới nhất |
| Điểm trung bình kỳ | v_ket_qua_hk.tb_hk | Hệ 4 |
| Xếp loại học lực | v_ket_qua_hk.xep_loai | xuat_sac, gioi, kha, trung_binh, yeu, kem |
| Tín chỉ tích lũy | v_ket_qua_hk.tc_tich_luy | Kỳ mới nhất |
| Điểm môn, điểm hệ 10 / hệ 4 / điểm chữ | v_diem.diem_10, diem_4, diem_chu | Môn học nhiều lần có nhiều dòng |
| Điểm chính thức của môn | v_diem với chinh_thuc = true | Lần có điểm cao nhất |
| Nợ môn, trượt môn | v_diem: chinh_thuc AND diem_chu = 'F' | |
| Chưa có điểm, hoãn thi | v_diem.diem_chu IN ('I', 'X') | |
| Học lại / học cải thiện | v_diem.loai_dk = 'hoc_lai' / 'cai_thien' | |
| Môn không tính điểm trung bình | v_diem.tinh_tb = false | GDTC, GDQP (điểm P/F) |
| Điểm rèn luyện | v_ket_qua_hk.diem_rl, xep_loai_rl | xuat_sac, tot, kha, trung_binh, yeu, kem |
| Cảnh báo học tập | v_ket_qua_hk.canh_bao | |
| Đủ điều kiện học bổng KKHT | v_xet_hb.du_dk_xet và các cột dk_* | Tính sẵn theo QĐ 725 |
| Điểm xét học bổng | v_xet_hb.tb_xet (hệ 4), tb_xet_10 | Chỉ HP học lần đầu, trừ GDTC/GDQP/CNTT/ngoại ngữ |
| Học bổng đã nhận | v_hoc_bong | |
| Tiền còn nợ, còn phải đóng | v_cong_no.con_no (theo kỳ), v_phai_thu.con_no (từng khoản) | |
| Học phí từng môn, vì sao học phí là X | v_hoc_phi: so_tien = n_hp × he_so_lop × don_gia | |
| Đơn giá tín chỉ | v_don_gia | nhom_mon = 'gdtc_gdqp' là giá riêng GDTC/GDQP của CTĐT tiếng Anh |
| Hệ số quy đổi tín chỉ học phí | ref_he_so_tc | lt 1,0; dac_thu 1,5; th 2,5 |
| Số dư tài khoản | v_so_du | |
| Lịch sử nộp tiền | v_giao_dich | |
| Miễn giảm học phí, chính sách đang hưởng | v_chinh_sach | trang_thai = 'dang_huong' |
| Mức trần miễn giảm | ref_muc_tran JOIN v_sinh_vien ON ma_khoi | |
| Kỷ luật | v_ky_luat | con_hieu_luc |
| Còn thiếu môn nào để tốt nghiệp | v_tien_do (trang_thai <> 'da_dat') + v_tot_nghiep | |
| Chuẩn đầu ra ngoại ngữ, GDTC, GDQP | v_tot_nghiep | loai: ngoai_ngu, cntt, gdtc, gdqp |
| Khóa, ngành, CTĐT của em | v_sinh_vien | |
| Thời khóa biểu, lịch học, học ở phòng nào | v_lich_hoc | thu 2..7 = thứ Hai..thứ Bảy, 8 = Chủ nhật |
| Lịch thi, số báo danh, có được dự thi không | v_lich_thi | du_dieu_kien, ly_do |
| Thực tập ở đâu, giảng viên hướng dẫn | v_thuc_tap | |"""

# Mô tả từng view; danh sách cột + kiểu lấy từ information_schema lúc chạy
VIEW_DOCS = {
    "v_sinh_vien": "Hồ sơ học vụ, 1 dòng: khoa, ngành, ma_khoi (nối ref_muc_tran), CTĐT, bậc, khóa (ten_khoa 'Cử nhân K19'), "
                   "hình thức, loai_ctdt (dai_tra|tieng_anh), tc_yeu_cau (TC tốt nghiệp), hk_thiet_ke, hb_dau_vao. "
                   "trang_thai: dang_hoc, bao_luu, dinh_chi, thoi_hoc, tot_nghiep.",
    "v_diem": "Điểm từng lần học mỗi học phần. lan_hoc 1 = học lần đầu; loai_dk: lan_dau, hoc_lai, cai_thien, hoc_doi; "
              "loai_hk: chinh|phu; ma_hk_chinh = HK chính mà HK phụ được gộp vào; dat: đạt hay không; "
              "chinh_thuc = lần học dùng tính TB tích lũy; loai_mon: thuong, gdtc, gdqp, cntt, ngoai_ngu, thuc_tap, do_an.",
    "v_ket_qua_hk": "Kết quả chính thức theo HK chính: tín chỉ đăng ký/đạt/trượt, TB học kỳ, TB và TC tích lũy (hệ 4), "
                    "xếp loại học lực, nam_thu, canh_bao, điểm và xếp loại rèn luyện.",
    "v_xet_hb": "Điều kiện THAM GIA xét học bổng KKHT theo từng HK chính (QĐ 725 Điều 4, 7): tc_xet, tb_xet (hệ 4), tb_xet_10, "
                "diem_thap_nhat, rèn luyện, các cờ dk_tb (TB ≥ 2,5), dk_rl (RL từ Tốt), dk_khong_duoi_2, dk_so_tc (≥ 15 TC, HK cuối ≥ 7), "
                "trong_thiet_ke; du_dk_xet tổng hợp; xep_loai_hb: xuat_sac|gioi|kha khi đủ điều kiện. "
                "Chiều của cờ: dk_*, trong_thiet_ke = true là ĐẠT; bi_ky_luat, co_hb_haui = true là BỊ LOẠI khỏi xét.",
    "v_tien_do": "Tiến độ CTĐT: mỗi học phần trong CTĐT, bat_buoc hay thuộc nhom_tu_chon (tc_nhom = số TC phải chọn), hk_thu theo kế hoạch, "
                 "trang_thai: da_dat, chua_dat, chua_hoc, chua_co_diem.",
    "v_tot_nghiep": "Điều kiện tốt nghiệp ngoài tín chỉ: loai (ngoai_ngu, cntt, gdtc, gdqp), dat, ngay_dat, ghi_chu (chứng chỉ).",
    "v_hoc_phi": "Học phí từng lớp học phần: n_hp (số TC học phí), he_so_lop, don_gia, so_tien = n_hp × he_so_lop × don_gia, han_nop.",
    "v_phai_thu": "Từng khoản phải nộp (loai: hoc_phi, khoan_thu, phi_phat, khac) với noi_dung, so_tien, da_tra, con_no, han_nop.",
    "v_cong_no": "Công nợ theo học kỳ: phai_thu, hoc_phi, khoan_khac, da_tra, con_no, han_nop (hạn sớm nhất của khoản còn nợ).",
    "v_giao_dich": "Lịch sử giao dịch tài khoản: loai (nap_tien, rut_tien, thanh_toan, hoan_tien, nhan_hb, nhan_mghp, nhan_ho_tro), "
                   "chieu (vao|ra), trang_thai (thanh_cong, that_bai, dang_xu_ly), kenh.",
    "v_so_du": "Số dư tài khoản cá nhân, 1 dòng.",
    "v_don_gia": "Đơn giá 1 tín chỉ học phí áp dụng cho sinh viên theo năm học; don_vi tc|thang|nam.",
    "v_hoc_bong": "Học bổng đã nhận: loai_hb, nhom (haui, kkht, thac_si, tai_tro, ntb), đợt (hoc_ky hoặc nam_hoc), xep_loai, so_tien, so_qd.",
    "v_chinh_sach": "Chính sách miễn giảm, hỗ trợ đang/đã hưởng: nhom (mien_hp, giam_hp, ho_tro_cp, noi_tru, ho_tro_ht, ho_tro_haui), "
                    "ty_le, co_so (muc_tran, luong_co_so, hoc_phi, khac), can_cu, thời hạn, trang_thai (dang_huong, tam_dung, ket_thuc).",
    "v_ky_luat": "Quyết định kỷ luật: hinh_thuc (khien_trach, canh_cao, dinh_chi, buoc_thoi_hoc), het_hieu_luc, con_hieu_luc. Không có nội dung vi phạm.",
    "v_lich_hoc": "Lịch học hằng tuần các lớp học phần đang đăng ký: thu, tiet_bd..tiet_kt, phong, tuan_bd..tuan_kt, giang_vien.",
    "v_lich_thi": "Lịch thi: thoi_gian, so_phut, hinh_thuc (tu_luan, trac_nghiem, van_dap, thuc_hanh, tieu_luan), phong, so_bd, vi_tri, "
                  "du_dieu_kien, ly_do (khi không đủ điều kiện dự thi).",
    "v_thuc_tap": "Thực tập doanh nghiệp: doanh_nghiep, dia_chi, linh_vuc, hoc_phan, gv_huong_dan, vi_tri, thời gian, "
                  "trang_thai (dang_thuc_tap, hoan_thanh, huy), diem.",
    "ref_thang_diem": "Thang quy đổi điểm chữ ↔ hệ 10 (tu..den) ↔ hệ 4; dat, tinh_tb.",
    "ref_he_so_tc": "Hệ số quy đổi tín chỉ học phí theo loai_tc (lt, dac_thu, th).",
    "ref_don_gia": "Bảng đơn giá chung theo năm học, bậc, khóa [khoa_tu, khoa_den], hình thức, loại CTĐT.",
    "ref_khoan_thu": "Các khoản thu ngoài học phí (BHYT, bảo hiểm thân thể, khám sức khỏe...) theo năm học, bậc.",
    "ref_muc_tran": "Mức trần miễn giảm học phí theo khối ngành (ma_khoi), năm học: muc_thang (đồng/tháng).",
    "ref_loai_hb": "Danh mục loại học bổng và văn bản căn cứ.",
    "ref_muc_hb": "Mức học bổng theo loại, năm học, xếp loại (một số mức là số minh họa, xem ghi_chu).",
    "ref_chinh_sach": "Danh mục chính sách miễn giảm, hỗ trợ.",
    "ref_hoc_ky": "Danh mục học kỳ: ma_hk, nam_hoc, loai (chinh|phu), ten, ma_hk_chinh, ngày bắt đầu/kết thúc.",
}

SYSTEM = RULES + """

Bảng thuật ngữ:
{glossary}

Các view được phép dùng (tên — mô tả — cột):
{schema}

Trả về: sql (câu SQL, không markdown) hoặc khong_ho_tro; gia_dinh nếu có cách hiểu cần nói rõ."""

HUMAN = """Câu hỏi: {question}{feedback}"""

FEEDBACK = """

Lần sinh trước bị lỗi, hãy sửa:
SQL trước: {sql}
Lỗi: {error}"""
