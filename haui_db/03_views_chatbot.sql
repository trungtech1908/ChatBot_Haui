-- =====================================================================
-- Schema chatbot: thứ DUY NHẤT text2sql nhìn thấy.
--
-- App mở transaction, gọi SELECT set_config('app.ma_sv', '<ma_sv đăng nhập>', true);
-- rồi mới chạy SQL do LLM sinh trong cùng transaction (db/session.py: chatbot_scope).
-- ⚠ Validator phải chặn set_config / SET / RESET trong SQL của LLM.
--
-- v_*   : dữ liệu của SV đang đăng nhập
-- ref_* : dữ liệu chung (đơn giá, khoản thu, thang điểm, ...)
--
-- BẢN TÀI LIỆU. Nguồn chính khi chạy: backend/src/chatbot_haui/db/sql/views.sql (Alembic execute).
-- Sửa view thì sửa file kia rồi chép sang đây.
-- =====================================================================
SET search_path = core;

CREATE OR REPLACE FUNCTION chatbot.ma_sv() RETURNS VARCHAR
LANGUAGE sql STABLE AS $$ SELECT NULLIF(current_setting('app.ma_sv', true), '') $$;

-- Hồ sơ học vụ (1 dòng, không có thông tin cá nhân)
CREATE VIEW chatbot.v_sinh_vien WITH (security_barrier) AS
SELECT sv.ma_sv, sv.ho_ten, sv.lop, sv.ngay_nhap_hoc, sv.trang_thai,
       k.ten AS khoa, n.ten AS nganh, n.ma_khoi, c.ma_ctdt, c.ten AS ctdt,   -- ma_khoi: nối ref_muc_tran
       nk.bac, nk.so_khoa,
       CASE nk.bac WHEN 'dai_hoc' THEN 'Cử nhân K' WHEN 'ky_su' THEN 'Kỹ sư K' ELSE 'Cao đẳng K' END || nk.so_khoa AS ten_khoa,
       nk.nam_nhap_hoc, c.hinh_thuc, c.loai AS loai_ctdt, c.so_tc AS tc_yeu_cau, c.so_hk AS hk_thiet_ke,
       sv.hb_dau_vao
FROM sinh_vien sv
JOIN ctdt c       ON c.ma_ctdt = sv.ma_ctdt
JOIN nganh n      ON n.ma_nganh = c.ma_nganh
JOIN khoa k       ON k.ma_khoa = n.ma_khoa
JOIN nien_khoa nk ON nk.ma_nk = c.ma_nk
WHERE sv.ma_sv = chatbot.ma_sv();

-- Điểm từng lần học. Điểm dùng tính TB tích lũy: chinh_thuc = true
CREATE VIEW chatbot.v_diem WITH (security_barrier) AS
SELECT d.ma_hk, hk.ten AS hoc_ky, hk.nam_hoc, hk.loai AS loai_hk, hk.ma_hk_chinh,
       d.ma_mon, m.ten AS mon, m.so_tc, m.loai AS loai_mon,
       d.lan_hoc, dk.loai AS loai_dk,
       d.diem_qt, d.diem_thi, d.diem_10, d.diem_chu, t.diem_4, t.dat,
       (m.tinh_tb AND t.tinh_tb) AS tinh_tb,
       m.xet_hb,
       d.chinh_thuc
FROM diem_hp d
JOIN mon m     ON m.ma_mon = d.ma_mon
JOIN hoc_ky hk ON hk.ma_hk = d.ma_hk
LEFT JOIN thang_diem t ON t.diem_chu = d.diem_chu
LEFT JOIN dang_ky dk   ON dk.ma_sv = d.ma_sv AND dk.ma_lop = d.ma_lop
WHERE d.ma_sv = chatbot.ma_sv();

-- Kết quả chính thức theo HK chính + rèn luyện
CREATE VIEW chatbot.v_ket_qua_hk WITH (security_barrier) AS
SELECT k.ma_hk, hk.ten AS hoc_ky, hk.nam_hoc,
       k.tc_dk, k.tc_dat, k.tc_truot, k.tb_hk, k.tc_tich_luy, k.tb_tich_luy,
       k.xep_loai, k.nam_thu, k.canh_bao,
       rl.diem AS diem_rl, rl.xep_loai AS xep_loai_rl
FROM ket_qua_hk k
JOIN hoc_ky hk ON hk.ma_hk = k.ma_hk
LEFT JOIN ren_luyen rl ON rl.ma_sv = k.ma_sv AND rl.ma_hk = k.ma_hk
WHERE k.ma_sv = chatbot.ma_sv();

-- ---------------------------------------------------------------------
-- Điều kiện tham gia xét HB KKHT theo HK chính — QĐ 725/QĐ-ĐHCN
--   Điều 4 k2: chỉ học phần học lần đầu (gồm HK phụ gộp vào); loại GDTC, GDQP, CNTT, ngoại ngữ
--   Điều 7 k1: TB xét ≥ 2.5; RL ≥ Tốt; không HP nào < 2.0; ≥ 15 TC (HK cuối ≥ 7 TC)
--   Điều 7 k3: xếp loại HB
-- Chỉ là điều kiện THAM GIA xét; HB xét theo quỹ, từ cao xuống thấp.
-- Chưa xử lý: ngoại lệ "trường bố trí không đủ 15 TC", kéo dài do bảo lưu.
-- ---------------------------------------------------------------------
CREATE VIEW chatbot.v_xet_hb WITH (security_barrier) AS
WITH sv AS (
    SELECT s.ma_sv, nk.nam_nhap_hoc, c.so_hk
    FROM sinh_vien s
    JOIN ctdt c       ON c.ma_ctdt = s.ma_ctdt
    JOIN nien_khoa nk ON nk.ma_nk = c.ma_nk
    WHERE s.ma_sv = chatbot.ma_sv()
),
hp AS (
    SELECT hk.ma_hk_chinh AS ma_hk, m.so_tc, d.diem_10, t.diem_4,
           (d.lan_hoc = 1 AND m.xet_hb AND m.tinh_tb) AS tinh_xet
    FROM diem_hp d
    JOIN sv            ON sv.ma_sv = d.ma_sv
    JOIN hoc_ky hk     ON hk.ma_hk = d.ma_hk
    JOIN mon m         ON m.ma_mon = d.ma_mon
    JOIN thang_diem t  ON t.diem_chu = d.diem_chu AND t.tinh_tb
),
agg AS (
    SELECT ma_hk,
           SUM(so_tc) FILTER (WHERE tinh_xet) AS tc_xet,
           ROUND(SUM(diem_4 * so_tc) FILTER (WHERE tinh_xet) / NULLIF(SUM(so_tc) FILTER (WHERE tinh_xet), 0), 2) AS tb_xet,
           ROUND(SUM(diem_10 * so_tc) FILTER (WHERE tinh_xet) / NULLIF(SUM(so_tc) FILTER (WHERE tinh_xet), 0), 2) AS tb_xet_10,
           MIN(diem_4) AS diem_thap_nhat   -- ⚠ quy chế không rõ phạm vi; đang lấy mọi HP có điểm quy đổi trong kỳ
    FROM hp GROUP BY ma_hk
),
base AS (
    SELECT a.*, hk.ten AS hoc_ky, hk.ngay_bd, hk.ngay_kt,
           (LEFT(a.ma_hk, 4)::int - sv.nam_nhap_hoc) * 2 + RIGHT(a.ma_hk, 1)::int AS hk_thu,
           sv.so_hk, rl.diem AS diem_rl, rl.xep_loai AS xep_loai_rl
    FROM agg a
    CROSS JOIN sv
    JOIN hoc_ky hk ON hk.ma_hk = a.ma_hk
    LEFT JOIN ren_luyen rl ON rl.ma_sv = sv.ma_sv AND rl.ma_hk = a.ma_hk
),
dk AS (
    SELECT b.*,
           COALESCE(b.tb_xet >= 2.5, false)                                   AS dk_tb,
           COALESCE(b.xep_loai_rl IN ('xuat_sac', 'tot'), false)              AS dk_rl,
           COALESCE(b.diem_thap_nhat >= 2.0, false)                           AS dk_khong_duoi_2,
           COALESCE(b.tc_xet >= CASE WHEN b.hk_thu = b.so_hk THEN 7 ELSE 15 END, false) AS dk_so_tc,
           b.hk_thu <= b.so_hk                                                AS trong_thiet_ke,
           EXISTS (SELECT 1 FROM ky_luat kl
                   WHERE kl.ma_sv = chatbot.ma_sv() AND kl.ngay_qd <= b.ngay_kt
                     AND (kl.het_hieu_luc IS NULL OR kl.het_hieu_luc >= b.ngay_bd))  AS bi_ky_luat,
           EXISTS (SELECT 1 FROM hoc_bong h JOIN loai_hb l ON l.ma_loai = h.ma_loai
                   WHERE h.ma_sv = chatbot.ma_sv() AND l.nhom = 'haui' AND h.ma_hk = b.ma_hk) AS co_hb_haui
    FROM base b
)
SELECT ma_hk, hoc_ky, hk_thu, tc_xet, tb_xet, tb_xet_10, diem_thap_nhat, diem_rl, xep_loai_rl,
       dk_tb, dk_rl, dk_khong_duoi_2, dk_so_tc, trong_thiet_ke, bi_ky_luat, co_hb_haui,
       (dk_tb AND dk_rl AND dk_khong_duoi_2 AND dk_so_tc AND trong_thiet_ke
        AND NOT bi_ky_luat AND NOT co_hb_haui) AS du_dk_xet,
       CASE WHEN dk_tb AND dk_rl AND dk_khong_duoi_2 AND dk_so_tc AND trong_thiet_ke
                 AND NOT bi_ky_luat AND NOT co_hb_haui
            THEN CASE WHEN tb_xet >= 3.6 AND xep_loai_rl = 'xuat_sac' THEN 'xuat_sac'
                      WHEN tb_xet >= 3.2 THEN 'gioi'
                      ELSE 'kha' END
       END AS xep_loai_hb
FROM dk;

-- Tiến độ CTĐT: môn đã đạt / chưa đạt / chưa học
CREATE VIEW chatbot.v_tien_do WITH (security_barrier) AS
SELECT cm.ma_mon, m.ten AS mon, m.so_tc, cm.bat_buoc, nt.ten AS nhom_tu_chon, nt.so_tc AS tc_nhom,
       cm.hk_thu, d.diem_chu, d.ma_hk AS hk_hoc,
       CASE WHEN d.ma_mon IS NULL THEN 'chua_hoc'
            WHEN t.dat THEN 'da_dat'
            WHEN t.dat IS NULL THEN 'chua_co_diem'
            ELSE 'chua_dat' END AS trang_thai
FROM sinh_vien s
JOIN ctdt_mon cm          ON cm.ma_ctdt = s.ma_ctdt
JOIN mon m                ON m.ma_mon = cm.ma_mon
LEFT JOIN nhom_tu_chon nt ON nt.ma_nhom = cm.ma_nhom
LEFT JOIN LATERAL (
    SELECT x.ma_mon, x.diem_chu, x.ma_hk FROM diem_hp x
    WHERE x.ma_sv = s.ma_sv AND x.ma_mon = cm.ma_mon
    ORDER BY x.chinh_thuc DESC, x.lan_hoc DESC LIMIT 1
) d ON true
LEFT JOIN thang_diem t ON t.diem_chu = d.diem_chu
WHERE s.ma_sv = chatbot.ma_sv();

CREATE VIEW chatbot.v_tot_nghiep WITH (security_barrier) AS
SELECT loai, dat, ngay_dat, ghi_chu FROM dk_tot_nghiep WHERE ma_sv = chatbot.ma_sv();

-- Học phí từng lớp: so_tien = n_hp × he_so_lop × don_gia
CREATE VIEW chatbot.v_hoc_phi WITH (security_barrier) AS
SELECT p.id, p.ma_hk, hk.ten AS hoc_ky, l.ma_lop, m.ma_mon, m.ten AS mon, m.so_tc,
       p.n_hp, p.he_so_lop, p.don_gia, p.so_tien, p.han_nop, p.trang_thai
FROM phai_thu p
JOIN hoc_ky hk ON hk.ma_hk = p.ma_hk
JOIN lop_hp l  ON l.ma_lop = p.ma_lop
JOIN mon m     ON m.ma_mon = l.ma_mon
WHERE p.ma_sv = chatbot.ma_sv() AND p.loai = 'hoc_phi';

-- Mọi khoản phải nộp (học phí, khoản thu, phí) kèm số đã trả / còn nợ
CREATE VIEW chatbot.v_phai_thu WITH (security_barrier) AS
SELECT p.id, p.ma_hk, hk.ten AS hoc_ky, p.loai,
       COALESCE(m.ten, kt.ten) AS noi_dung,         -- tên môn hoặc tên khoản thu
       p.so_tien, p.han_nop,
       COALESCE(t.da_tra, 0)            AS da_tra,
       p.so_tien - COALESCE(t.da_tra, 0) AS con_no
FROM phai_thu p
JOIN hoc_ky hk          ON hk.ma_hk = p.ma_hk
LEFT JOIN lop_hp l      ON l.ma_lop = p.ma_lop
LEFT JOIN mon m         ON m.ma_mon = l.ma_mon
LEFT JOIN khoan_thu kt  ON kt.ma_kt = p.ma_kt
LEFT JOIN (SELECT ma_phai_thu, SUM(so_tien) AS da_tra FROM giao_dich
           WHERE loai = 'thanh_toan' AND trang_thai = 'thanh_cong' GROUP BY ma_phai_thu) t ON t.ma_phai_thu = p.id
WHERE p.ma_sv = chatbot.ma_sv() AND p.trang_thai = 'hieu_luc';

-- Công nợ theo học kỳ
CREATE VIEW chatbot.v_cong_no WITH (security_barrier) AS
WITH p AS (
    SELECT p.ma_hk, p.loai, p.so_tien, p.han_nop,
           COALESCE((SELECT SUM(g.so_tien) FROM giao_dich g
                     WHERE g.ma_phai_thu = p.id AND g.loai = 'thanh_toan' AND g.trang_thai = 'thanh_cong'), 0) AS da_tra
    FROM phai_thu p
    WHERE p.ma_sv = chatbot.ma_sv() AND p.trang_thai = 'hieu_luc'
)
SELECT p.ma_hk, hk.ten AS hoc_ky,
       SUM(p.so_tien)                                    AS phai_thu,
       SUM(p.so_tien) FILTER (WHERE p.loai = 'hoc_phi')  AS hoc_phi,
       SUM(p.so_tien) FILTER (WHERE p.loai <> 'hoc_phi') AS khoan_khac,
       SUM(p.da_tra)                                     AS da_tra,
       SUM(p.so_tien) - SUM(p.da_tra)                    AS con_no,
       MIN(p.han_nop) FILTER (WHERE p.so_tien > p.da_tra) AS han_nop
FROM p JOIN hoc_ky hk ON hk.ma_hk = p.ma_hk
GROUP BY p.ma_hk, hk.ten;

CREATE VIEW chatbot.v_giao_dich WITH (security_barrier) AS
SELECT g.thoi_gian, g.loai, g.chieu, g.so_tien, g.trang_thai, g.kenh, g.ghi_chu, p.ma_hk
FROM giao_dich g
LEFT JOIN phai_thu p ON p.id = g.ma_phai_thu
WHERE g.ma_sv = chatbot.ma_sv();

-- Số dư tài khoản cá nhân
CREATE VIEW chatbot.v_so_du WITH (security_barrier) AS
SELECT COALESCE(SUM(CASE chieu WHEN 'vao' THEN so_tien ELSE -so_tien END), 0) AS so_du
FROM giao_dich
WHERE ma_sv = chatbot.ma_sv() AND trang_thai = 'thanh_cong';

-- Đơn giá áp dụng cho SV này
CREATE VIEW chatbot.v_don_gia WITH (security_barrier) AS
SELECT dg.nam_hoc, dg.nhom_mon, dg.don_gia, dg.don_vi, dg.so_qd
FROM sinh_vien s
JOIN ctdt c       ON c.ma_ctdt = s.ma_ctdt
JOIN nien_khoa nk ON nk.ma_nk = c.ma_nk
JOIN don_gia dg   ON dg.bac = nk.bac
                 AND nk.so_khoa BETWEEN dg.khoa_tu AND dg.khoa_den
                 AND dg.hinh_thuc = c.hinh_thuc
                 AND dg.loai_ctdt IN (c.loai, 'tat_ca')
WHERE s.ma_sv = chatbot.ma_sv();

CREATE VIEW chatbot.v_hoc_bong WITH (security_barrier) AS
SELECT l.ten AS loai_hb, l.nhom, h.ma_hk, hk.ten AS hoc_ky, h.nam_hoc, h.xep_loai,
       h.nha_tai_tro, h.so_tien, h.so_qd, h.ngay_qd
FROM hoc_bong h
JOIN loai_hb l      ON l.ma_loai = h.ma_loai
LEFT JOIN hoc_ky hk ON hk.ma_hk = h.ma_hk
WHERE h.ma_sv = chatbot.ma_sv();

CREATE VIEW chatbot.v_chinh_sach WITH (security_barrier) AS
SELECT cs.ten, cs.nhom, cs.ty_le, cs.co_so, cs.can_cu, x.tu_ngay, x.den_ngay, x.trang_thai, x.so_qd
FROM sv_chinh_sach x
JOIN chinh_sach cs ON cs.ma_cs = x.ma_cs
WHERE x.ma_sv = chatbot.ma_sv();

-- Không lộ nội dung vi phạm
CREATE VIEW chatbot.v_ky_luat WITH (security_barrier) AS
SELECT hinh_thuc, so_qd, ngay_qd, het_hieu_luc,
       (het_hieu_luc IS NULL OR het_hieu_luc >= CURRENT_DATE) AS con_hieu_luc
FROM ky_luat
WHERE ma_sv = chatbot.ma_sv();

-- ---------------------------------------------------------------------
-- Lịch học, lịch thi, thực tập (bảng bổ sung ngoài 01_schema.sql gốc)
-- Không đưa email/SĐT giảng viên vào view.
-- ---------------------------------------------------------------------

-- Lịch học hằng tuần của các lớp học phần SV đang đăng ký
CREATE VIEW chatbot.v_lich_hoc WITH (security_barrier) AS
SELECT l.ma_hk, hk.ten AS hoc_ky, l.ma_lop, m.ma_mon, m.ten AS mon,
       lh.thu, lh.tiet_bd, lh.so_tiet, lh.tiet_bd + lh.so_tiet - 1 AS tiet_kt,
       COALESCE(lh.phong, l.phong) AS phong, lh.tuan_bd, lh.tuan_kt,
       gv.ho_ten AS giang_vien, gv.hoc_vi
FROM dang_ky dk
JOIN lop_hp l    ON l.ma_lop = dk.ma_lop
JOIN lich_hoc lh ON lh.ma_lop = l.ma_lop
JOIN mon m       ON m.ma_mon = l.ma_mon
JOIN hoc_ky hk   ON hk.ma_hk = l.ma_hk
LEFT JOIN giang_vien gv ON gv.ma_gv = l.ma_gv
WHERE dk.ma_sv = chatbot.ma_sv() AND dk.trang_thai = 'dang_ky';

-- Lịch thi của SV: số báo danh, phòng, điều kiện dự thi
CREATE VIEW chatbot.v_lich_thi WITH (security_barrier) AS
SELECT l.ma_hk, hk.ten AS hoc_ky, lt.ma_lop, m.ma_mon, m.ten AS mon,
       lt.lan_thi, lt.thoi_gian, lt.so_phut, lt.hinh_thuc, lt.phong,
       x.so_bd, x.vi_tri, x.du_dieu_kien, x.ly_do
FROM lich_thi_sv x
JOIN lich_thi lt ON lt.id = x.ma_lich_thi
JOIN lop_hp l    ON l.ma_lop = lt.ma_lop
JOIN mon m       ON m.ma_mon = l.ma_mon
JOIN hoc_ky hk   ON hk.ma_hk = l.ma_hk
WHERE x.ma_sv = chatbot.ma_sv();

CREATE VIEW chatbot.v_thuc_tap WITH (security_barrier) AS
SELECT t.ma_hk, hk.ten AS hoc_ky, dn.ten AS doanh_nghiep, dn.dia_chi, dn.linh_vuc,
       m.ten AS hoc_phan, gv.ho_ten AS gv_huong_dan, gv.hoc_vi,
       t.vi_tri, t.tu_ngay, t.den_ngay, t.trang_thai, t.diem
FROM thuc_tap t
JOIN doanh_nghiep dn    ON dn.ma_dn = t.ma_dn
JOIN hoc_ky hk          ON hk.ma_hk = t.ma_hk
LEFT JOIN mon m         ON m.ma_mon = t.ma_mon
LEFT JOIN giang_vien gv ON gv.ma_gv = t.ma_gv
WHERE t.ma_sv = chatbot.ma_sv();

-- ---------------------------------------------------------------------
-- Tham chiếu chung
-- ---------------------------------------------------------------------
CREATE VIEW chatbot.ref_thang_diem AS SELECT * FROM thang_diem;
CREATE VIEW chatbot.ref_he_so_tc   AS SELECT * FROM he_so_tc;
CREATE VIEW chatbot.ref_don_gia    AS SELECT nam_hoc, bac, khoa_tu, khoa_den, hinh_thuc, loai_ctdt, nhom_mon,
                                             don_gia, don_vi, so_qd FROM don_gia;
CREATE VIEW chatbot.ref_khoan_thu  AS SELECT * FROM khoan_thu;
CREATE VIEW chatbot.ref_muc_tran   AS SELECT m.ma_khoi, k.bac, k.ten AS khoi_nganh, m.nam_hoc, m.muc_thang
                                      FROM muc_tran m JOIN khoi_nganh k USING (ma_khoi);
CREATE VIEW chatbot.ref_loai_hb    AS SELECT * FROM loai_hb;
CREATE VIEW chatbot.ref_muc_hb     AS SELECT l.ten AS loai_hb, m.nam_hoc, m.xep_loai, m.so_tien, m.ty_le, m.ghi_chu
                                      FROM muc_hb m JOIN loai_hb l USING (ma_loai);
CREATE VIEW chatbot.ref_chinh_sach AS SELECT * FROM chinh_sach;
CREATE VIEW chatbot.ref_hoc_ky     AS SELECT ma_hk, nam_hoc, loai, ten, ma_hk_chinh, ngay_bd, ngay_kt FROM hoc_ky;

-- =====================================================================
-- PHÂN QUYỀN — app kết nối bằng login role thuộc chatbot_reader
-- =====================================================================
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'chatbot_reader') THEN
        CREATE ROLE chatbot_reader NOLOGIN;
    END IF;
END $$;

REVOKE ALL ON SCHEMA core, private FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA core, private FROM PUBLIC;
GRANT USAGE ON SCHEMA chatbot TO chatbot_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA chatbot TO chatbot_reader;
GRANT EXECUTE ON FUNCTION chatbot.ma_sv() TO chatbot_reader;
ALTER ROLE chatbot_reader SET statement_timeout = '5s';
