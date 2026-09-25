-- =====================================================================
-- Dữ liệu tham số lấy từ văn bản quy chế. Năm học mới → INSERT dòng mới, không sửa dòng cũ.
-- =====================================================================
SET search_path = core;

-- Thang điểm — QCĐT Điều 9 k7, Điều 10 k2
INSERT INTO thang_diem (diem_chu, tu, den, diem_4, dat, tinh_tb, mo_ta) VALUES
('A',  8.5, 10.0, 4.0,  true,  true,  'Đạt, 8,5–10,0'),
('B+', 7.7,  8.4, 3.5,  true,  true,  'Đạt, 7,7–8,4'),
('B',  7.0,  7.6, 3.0,  true,  true,  'Đạt, 7,0–7,6'),
('C+', 6.2,  6.9, 2.5,  true,  true,  'Đạt, 6,2–6,9'),
('C',  5.5,  6.1, 2.0,  true,  true,  'Đạt, 5,5–6,1'),
('D+', 4.7,  5.4, 1.5,  true,  true,  'Đạt, 4,7–5,4'),
('D',  4.0,  4.6, 1.0,  true,  true,  'Đạt, 4,0–4,6'),
('F',  0.0,  3.9, 0.0,  false, true,  'Không đạt, dưới 4,0; phải học lại'),
('P',  5.0, 10.0, NULL, true,  false, 'Đạt không phân mức, từ 5,0; không tính TB'),
('I',  NULL, NULL, NULL, NULL, false, 'Chưa hoàn thiện do được hoãn thi'),
('X',  NULL, NULL, NULL, NULL, false, 'Chưa hoàn thiện do chưa đủ dữ liệu'),
('R',  NULL, NULL, NULL, true, false, 'Miễn học, công nhận tín chỉ');

-- Hệ số TC học phí — QĐ tính học phí, Điều 1
INSERT INTO he_so_tc (loai_tc, he_so, mo_ta) VALUES
('lt',      1.0, 'Lý thuyết, tiểu luận/BTL; GDTC, GDQP'),
('dac_thu', 1.5, 'Ngoại ngữ, thực tập, đồ án/khóa luận'),
('th',      2.5, 'Thực hành, thí nghiệm');

-- Đơn giá 2025-2026 — QĐ 778/QĐ-ĐHCN
INSERT INTO don_gia (nam_hoc, bac, khoa_tu, khoa_den, hinh_thuc, loai_ctdt, nhom_mon, don_gia, don_vi, so_qd) VALUES
('2025-2026', 'dai_hoc',  20, 20, 'chinh_quy', 'tieng_anh', 'tat_ca',    1000000, 'tc',    '778/QĐ-ĐHCN'),
('2025-2026', 'dai_hoc',  20, 20, 'chinh_quy', 'tieng_anh', 'gdtc_gdqp',  700000, 'tc',    '778/QĐ-ĐHCN'),
('2025-2026', 'dai_hoc',  20, 20, 'chinh_quy', 'dai_tra',   'tat_ca',     700000, 'tc',    '778/QĐ-ĐHCN'),
('2025-2026', 'dai_hoc',  19, 19, 'chinh_quy', 'tat_ca',    'tat_ca',     550000, 'tc',    '778/QĐ-ĐHCN'),
('2025-2026', 'dai_hoc',   1, 18, 'chinh_quy', 'tat_ca',    'tat_ca',     495000, 'tc',    '778/QĐ-ĐHCN'),
('2025-2026', 'ky_su',     3,  3, 'chinh_quy', 'tieng_anh', 'tat_ca',    1000000, 'tc',    '778/QĐ-ĐHCN'),
('2025-2026', 'ky_su',     3,  3, 'chinh_quy', 'tieng_anh', 'gdtc_gdqp',  700000, 'tc',    '778/QĐ-ĐHCN'),
('2025-2026', 'ky_su',     3,  3, 'chinh_quy', 'dai_tra',   'tat_ca',     700000, 'tc',    '778/QĐ-ĐHCN'),
('2025-2026', 'ky_su',     2,  2, 'chinh_quy', 'tat_ca',    'tat_ca',     550000, 'tc',    '778/QĐ-ĐHCN'),
('2025-2026', 'ky_su',     1,  1, 'chinh_quy', 'tat_ca',    'tat_ca',     495000, 'tc',    '778/QĐ-ĐHCN'),
('2025-2026', 'dai_hoc',   1, 99, 'tu_xa',     'tat_ca',    'tat_ca',     495000, 'tc',    '778/QĐ-ĐHCN'),
('2025-2026', 'dai_hoc',   1, 99, 'vlvh',      'tat_ca',    'tat_ca',    2400000, 'thang', '778/QĐ-ĐHCN'),
('2025-2026', 'cao_dang',  1, 99, 'chinh_quy', 'tat_ca',    'tat_ca',     370000, 'tc',    '778/QĐ-ĐHCN');

-- Khoản thu 2025-2026 — QĐ 1659/QĐ-ĐHCN
-- ⚠ Bảng gốc bị OCR lệch cột. Đối chiếu bản PDF trước khi dùng thật.
INSERT INTO khoan_thu (ma_kt, ten, nam_hoc, bac, so_tien, chu_ky, tu_ngay, den_ngay, ghi_chu, so_qd) VALUES
('2526_BHYT15_DH', 'Bảo hiểm y tế',     '2025-2026', 'dai_hoc',  789750, '15 tháng',  '2025-10-01', '2026-12-31', NULL, '1659/QĐ-ĐHCN'),
('2526_BHYT12_DH', 'Bảo hiểm y tế',     '2025-2026', 'dai_hoc',  631800, '12 tháng',  '2026-01-01', '2026-12-31', NULL, '1659/QĐ-ĐHCN'),
('2526_BHYT12_KS', 'Bảo hiểm y tế',     '2025-2026', 'ky_su',    642330, '12 tháng',  '2025-08-01', '2026-07-31', NULL, '1659/QĐ-ĐHCN'),
('2526_BHTT_DH',   'Bảo hiểm thân thể', '2025-2026', 'dai_hoc',  325000, '4 năm học', NULL, NULL,
 'Miễn cho con liệt sỹ, thương binh, bệnh binh hạng 1/4; giảm 50% cho đối tượng chính sách', '1659/QĐ-ĐHCN'),
('2526_BHTT_KS',   'Bảo hiểm thân thể', '2025-2026', 'ky_su',     95000, '1 năm học', NULL, NULL, NULL, '1659/QĐ-ĐHCN'),
('2526_BHTT_CD',   'Bảo hiểm thân thể', '2025-2026', 'cao_dang', 255000, '3 năm học', NULL, NULL, NULL, '1659/QĐ-ĐHCN'),
('2526_BHLD_DH',   'Bảo hộ lao động (ngành kỹ thuật, công nghệ)', '2025-2026', 'dai_hoc', 400000, '2 bộ/khóa học', NULL, NULL, NULL, '1659/QĐ-ĐHCN'),
('2526_KSK_DH',    'Khám sức khỏe',     '2025-2026', 'dai_hoc',  120000, 'lần',       NULL, NULL, NULL, '1659/QĐ-ĐHCN'),
('2526_QKH_DH',    'Quỹ khuyến học',    '2025-2026', 'dai_hoc',   20000, 'khóa học',  NULL, NULL, NULL, '1659/QĐ-ĐHCN'),
('PHI_XEM_LAI',    'Phí đăng ký nhưng không đến xem lại bài thi', NULL, 'tat_ca', 50000, 'lượt', '2025-01-01', NULL,
 'Trừ vào tài khoản cá nhân trên ĐH điện tử', 'Thông báo TTKT');

-- Khối ngành & mức trần MGHP (nghìn đồng → VND) — Quy định chính sách SV, Điều 3
INSERT INTO khoi_nganh (ma_khoi, bac, ten) VALUES
('DH_NGHE_THUAT',  'dai_hoc',  'Nghệ thuật'),
('DH_KD_QL_PL',    'dai_hoc',  'Kinh doanh và quản lý, pháp luật'),
('DH_CNTT_KT',     'dai_hoc',  'Máy tính và CNTT, công nghệ kỹ thuật, kỹ thuật, sản xuất và chế biến'),
('DH_SUC_KHOE',    'dai_hoc',  'Các khối ngành sức khỏe khác'),
('DH_NHAN_VAN_XH', 'dai_hoc',  'Nhân văn, KHXH và hành vi, báo chí, dịch vụ xã hội, du lịch, khách sạn'),
('CD_XHNV_KD',     'cao_dang', 'KHXH nhân văn, nghệ thuật, giáo dục, báo chí, kinh doanh, quản lý'),
('CD_KT_CNTT',     'cao_dang', 'Kỹ thuật và công nghệ thông tin'),
('CD_DV_DL_MT',    'cao_dang', 'Dịch vụ, du lịch và môi trường');

INSERT INTO muc_tran (ma_khoi, nam_hoc, muc_thang)
SELECT ma_khoi, nam_hoc, muc * 1000
FROM (VALUES
  ('DH_NGHE_THUAT',  1200, 1350, 1520, 1710),
  ('DH_KD_QL_PL',    1250, 1410, 1590, 1790),
  ('DH_CNTT_KT',     1450, 1640, 1850, 2090),
  ('DH_SUC_KHOE',    1850, 2090, 2360, 2660),
  ('DH_NHAN_VAN_XH', 1200, 1500, 1690, 1910),
  ('CD_XHNV_KD',     1248, 1328, 1360, 1600),
  ('CD_KT_CNTT',     1870, 1992, 2040, 2400),
  ('CD_DV_DL_MT',    1560, 1660, 1700, 2000)
) AS v(ma_khoi, y2324, y2425, y2526, y2627)
CROSS JOIN LATERAL (VALUES ('2023-2024', y2324), ('2024-2025', y2425),
                           ('2025-2026', y2526), ('2026-2027', y2627)) AS n(nam_hoc, muc);

-- Loại HB — QĐ 725/QĐ-ĐHCN, QĐ 279/QĐ-ĐHCN
INSERT INTO loai_hb (ma_loai, ten, nhom, chu_ky, van_ban) VALUES
('HAUI_TOAN_KHOA', 'Học bổng HaUI toàn khóa học',                    'haui',    'hoc_ky',  'QĐ 725/QĐ-ĐHCN, Điều 5–6'),
('HAUI_NAM_NHAT',  'Học bổng HaUI năm thứ nhất',                     'haui',    'hoc_ky',  'QĐ 725/QĐ-ĐHCN, Điều 5–6'),
('HAUI_5TR',       'Học bổng HaUI 5 triệu đồng/suất',                'haui',    'nam_hoc', 'QĐ 725/QĐ-ĐHCN, Điều 5'),
('KKHT',           'Học bổng khuyến khích học tập',                  'kkht',    'hoc_ky',  'QĐ 725/QĐ-ĐHCN, Điều 7'),
('KKHT_THAC_SI',   'Học bổng KKHT cho SV học trước học phần Thạc sĩ', 'thac_si', 'hoc_ky',  'QĐ 725/QĐ-ĐHCN, Điều 8'),
('TAI_TRO',        'Học bổng tài trợ',                               'tai_tro', 'nam_hoc', 'QĐ 725/QĐ-ĐHCN, Điều 9–11'),
('NTB',            'Học bổng khuyến học Nguyễn Thanh Bình',          'ntb',     'nam_hoc', 'QĐ 279/QĐ-ĐHCN');

-- Mức KKHT (Quy chế chi tiêu nội bộ) và NTB (Hiệu trưởng quyết định) chưa có trong văn bản → bổ sung sau
INSERT INTO muc_hb (ma_loai, nam_hoc, xep_loai, so_tien, ty_le, ghi_chu) VALUES
('HAUI_TOAN_KHOA', '2025-2026', 'chung', NULL,    1.000, '100% học phí học phần học lần đầu'),
('HAUI_NAM_NHAT',  '2025-2026', 'chung', NULL,    1.000, '100% học phí học phần học lần đầu, năm thứ nhất'),
('HAUI_5TR',       '2025-2026', 'chung', 5000000, NULL,  NULL),
('KKHT_THAC_SI',   '2025-2026', 'chung', NULL,    0.300, '30% học phí học phần học trước, đơn giá Thạc sĩ, tối đa 15 TC');

-- Đối tượng — Quy định chính sách SV; QĐ 279 mục 2.1
INSERT INTO doi_tuong (ma_dt, ten) VALUES
('nguoi_co_cong',        'Người có công với cách mạng hoặc thân nhân'),
('khuyet_tat',           'Người khuyết tật'),
('khong_noi_nuong_tua',  'Mồ côi cả cha mẹ / không nơi nương tựa (Điều 4 khoản 3, ≤ 22 tuổi)'),
('mo_coi_1',             'Mồ côi bố hoặc mẹ'),
('ho_ngheo',             'Thuộc hộ nghèo (theo năm công nhận)'),
('ho_can_ngheo',         'Thuộc hộ cận nghèo (theo năm công nhận)'),
('dtts',                 'Người dân tộc thiểu số'),
('dtts_rat_it_nguoi',    'Người dân tộc thiểu số rất ít người'),
('vung_kho_khan',        'Cư trú tại vùng KT-XH khó khăn / đặc biệt khó khăn'),
('cha_me_tnld',          'Cha/mẹ bị TNLĐ hoặc bệnh nghề nghiệp hưởng trợ cấp thường xuyên'),
('benh_hiem_ngheo',      'Mắc bệnh hiểm nghèo'),
('cha_me_benh_nang',     'Bố/mẹ mắc bệnh hiểm nghèo hoặc mất khả năng lao động'),
('kho_khan_dac_biet',    'Hoàn cảnh đặc biệt khó khăn');

INSERT INTO chinh_sach (ma_cs, ten, nhom, ty_le, co_so, so_thang, can_cu) VALUES
('MIEN_NCC',        'Miễn 100% HP — người có công và thân nhân',       'mien_hp',     1.000, 'muc_tran',    10, 'Điều 4 khoản 1'),
('MIEN_KT',         'Miễn 100% HP — người khuyết tật',                 'mien_hp',     1.000, 'muc_tran',    10, 'Điều 4 khoản 2'),
('MIEN_MO_COI',     'Miễn 100% HP — mồ côi/không nơi nương tựa',       'mien_hp',     1.000, 'muc_tran',    10, 'Điều 4 khoản 3'),
('MIEN_DTTS_NGHEO', 'Miễn 100% HP — DTTS thuộc hộ nghèo/cận nghèo',    'mien_hp',     1.000, 'muc_tran',    10, 'Điều 4 khoản 4'),
('MIEN_DTTS_RIN',   'Miễn 100% HP — DTTS rất ít người vùng khó khăn',  'mien_hp',     1.000, 'muc_tran',    10, 'Điều 4 khoản 5'),
('GIAM70_CD',       'Giảm 70% HP — một số ngành cao đẳng',             'giam_hp',     0.700, 'muc_tran',    10, 'Điều 5 khoản 1'),
('GIAM70_DTTS',     'Giảm 70% HP — DTTS vùng đặc biệt khó khăn',       'giam_hp',     0.700, 'muc_tran',    10, 'Điều 5 khoản 2'),
('GIAM50_TNLD',     'Giảm 50% HP — cha/mẹ bị TNLĐ, bệnh nghề nghiệp',  'giam_hp',     0.500, 'muc_tran',    10, 'Điều 5 khoản 3'),
('HT_CHI_PHI',      'Hỗ trợ chi phí học tập 60% lương cơ sở',          'ho_tro_cp',   0.600, 'luong_co_so', 10, 'Điều 10–11'),
('NOI_TRU_100',     'Nội trú 100% lương cơ sở',                        'noi_tru',     1.000, 'luong_co_so', 12, 'Chương IV'),
('NOI_TRU_80',      'Nội trú 80% lương cơ sở',                         'noi_tru',     0.800, 'luong_co_so', 12, 'Chương IV'),
('NOI_TRU_60',      'Nội trú 60% lương cơ sở',                         'noi_tru',     0.600, 'luong_co_so', 12, 'Chương IV'),
('HT_HOC_TAP',      'Hỗ trợ học tập DTTS rất ít người 100% lương cơ sở','ho_tro_ht',  1.000, 'luong_co_so', 12, 'Điều 20–21'),
('HT_HAUI',         'Hỗ trợ HaUI — tối đa bằng học phí học kỳ đề nghị', 'ho_tro_haui', NULL, 'hoc_phi',     NULL, 'Điều 25–26');

-- Lương cơ sở: văn bản không nêu số → nhập theo nghị định hiện hành
-- INSERT INTO tham_so (ma, gia_tri, tu_ngay, ghi_chu) VALUES ('luong_co_so', <giá trị>, '<ngày>', '<nghị định>');
