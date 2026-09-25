-- =====================================================================
-- CSDL hỏi đáp quy chế HaUI: học bổng, học phí, kết quả học tập
-- PostgreSQL 14+
--
-- BẢN TÀI LIỆU. Nguồn chính khi chạy: model SQLAlchemy + Alembic trong backend/.
--
-- Quy ước tên
--   ma_*  mã (khóa)        so_*  số lượng       tc  tín chỉ
--   hk    học kỳ           hb    học bổng       hp  học phần
--   nk    niên khóa        dt    đối tượng      cs  chính sách
--   qd    quyết định       bd/kt bắt đầu/kết thúc
--
-- Quy ước giá trị
--   Tiền: NUMERIC(12,0) VND | Điểm hệ 10: NUMERIC(3,1) | Điểm TB: NUMERIC(3,2)
--   ma_hk: 'YYYYk' — YYYY năm bắt đầu năm học; k = 1,2 HK chính, 3,4 HK phụ
--          VD '20251' = HK1 năm học 2025-2026
--
-- Schema
--   core    : dữ liệu nghiệp vụ
--   private : tài khoản đăng nhập. Không cấp quyền cho chatbot
--   chatbot : view cho text2sql (03_views_chatbot.sql)
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS private;
CREATE SCHEMA IF NOT EXISTS chatbot;
SET search_path = core;

-- =====================================================================
-- 1. DANH MỤC ĐÀO TẠO
-- =====================================================================

-- Đơn vị đào tạo (Khoa/Trường/Trung tâm)
CREATE TABLE khoa (
    ma_khoa  VARCHAR(10)  PRIMARY KEY,
    ten      VARCHAR(100) NOT NULL
);

-- Khối ngành để tra mức trần miễn giảm học phí (NĐ 97/2023)
CREATE TABLE khoi_nganh (
    ma_khoi  VARCHAR(20)  PRIMARY KEY,
    bac      VARCHAR(10)  NOT NULL CHECK (bac IN ('dai_hoc', 'cao_dang')),
    ten      VARCHAR(200) NOT NULL
);

CREATE TABLE nganh (
    ma_nganh  VARCHAR(10)  PRIMARY KEY,
    ten       VARCHAR(150) NOT NULL,
    ma_khoa   VARCHAR(10)  NOT NULL REFERENCES khoa,
    ma_khoi   VARCHAR(20)  NOT NULL REFERENCES khoi_nganh,
    khoi_ntb  VARCHAR(10)  NOT NULL CHECK (khoi_ntb IN ('ky_thuat', 'xa_hoi'))  -- khối chia quỹ HB Nguyễn Thanh Bình
);

-- Khóa tuyển sinh: "Cử nhân K19" = (dai_hoc, 19), "Kỹ sư K2" = (ky_su, 2)
CREATE TABLE nien_khoa (
    ma_nk         VARCHAR(10) PRIMARY KEY,     -- 'DH-K19'
    bac           VARCHAR(10) NOT NULL CHECK (bac IN ('dai_hoc', 'ky_su', 'cao_dang')),
    so_khoa       SMALLINT    NOT NULL,
    nam_nhap_hoc  SMALLINT    NOT NULL,
    UNIQUE (bac, so_khoa)
);

-- Chương trình đào tạo
CREATE TABLE ctdt (
    ma_ctdt    VARCHAR(15)  PRIMARY KEY,
    ten        VARCHAR(150) NOT NULL,
    ma_nganh   VARCHAR(10)  NOT NULL REFERENCES nganh,
    ma_nk      VARCHAR(10)  NOT NULL REFERENCES nien_khoa,
    hinh_thuc  VARCHAR(10)  NOT NULL CHECK (hinh_thuc IN ('chinh_quy', 'vlvh', 'tu_xa')),
    loai       VARCHAR(10)  NOT NULL CHECK (loai IN ('dai_tra', 'tieng_anh')),
    so_tc      SMALLINT     NOT NULL,     -- tổng TC yêu cầu tốt nghiệp
    so_hk      SMALLINT     NOT NULL      -- số HK thiết kế; HB chỉ xét trong khoảng này
);

CREATE TABLE hoc_ky (
    ma_hk        CHAR(5)     PRIMARY KEY,               -- '20251'
    nam_hoc      CHAR(9)     NOT NULL,                  -- '2025-2026'
    loai         VARCHAR(5)  NOT NULL CHECK (loai IN ('chinh', 'phu')),
    ten          VARCHAR(50) NOT NULL,                  -- 'Học kỳ 1 năm học 2025-2026'
    ma_hk_chinh  CHAR(5)     NOT NULL REFERENCES hoc_ky, -- HK chính mà kết quả được gộp vào (HK chính = chính nó)
    ngay_bd      DATE,
    ngay_kt      DATE,
    CHECK (loai = 'phu' OR ma_hk_chinh = ma_hk)
);

CREATE TABLE mon (
    ma_mon      VARCHAR(10)  PRIMARY KEY,
    ten         VARCHAR(150) NOT NULL,
    so_tc       SMALLINT     NOT NULL CHECK (so_tc > 0),
    -- Tín chỉ thành phần, dùng tính TC học phí
    tc_lt       NUMERIC(3,1) NOT NULL DEFAULT 0,   -- lý thuyết, tiểu luận/BTL, GDTC, GDQP  → hệ số 1,0
    tc_dac_thu  NUMERIC(3,1) NOT NULL DEFAULT 0,   -- ngoại ngữ, thực tập, đồ án            → hệ số 1,5
    tc_th       NUMERIC(3,1) NOT NULL DEFAULT 0,   -- thực hành, thí nghiệm                 → hệ số 2,5
    loai        VARCHAR(15)  NOT NULL DEFAULT 'thuong'
                CHECK (loai IN ('thuong', 'gdtc', 'gdqp', 'cntt', 'ngoai_ngu', 'thuc_tap', 'do_an')),
    tinh_tb     BOOLEAN      NOT NULL DEFAULT true,  -- false: chỉ xếp P/F, không tính điểm TB
    xet_hb      BOOLEAN      NOT NULL DEFAULT true,  -- false: GDTC, GDQP, CNTT, ngoại ngữ... không tính điểm xét HB
    CHECK (tc_lt + tc_dac_thu + tc_th = so_tc)
);

CREATE TABLE nhom_tu_chon (
    ma_nhom  VARCHAR(15)  PRIMARY KEY,
    ma_ctdt  VARCHAR(15)  NOT NULL REFERENCES ctdt,
    ten      VARCHAR(100) NOT NULL,
    so_tc    SMALLINT     NOT NULL      -- số TC phải chọn trong nhóm
);

-- Môn thuộc CTĐT
CREATE TABLE ctdt_mon (
    ma_ctdt   VARCHAR(15) NOT NULL REFERENCES ctdt,
    ma_mon    VARCHAR(10) NOT NULL REFERENCES mon,
    bat_buoc  BOOLEAN     NOT NULL,
    ma_nhom   VARCHAR(15) REFERENCES nhom_tu_chon,   -- NULL nếu bắt buộc
    hk_thu    SMALLINT,                               -- học kỳ thứ mấy theo kế hoạch chuẩn
    PRIMARY KEY (ma_ctdt, ma_mon),
    CHECK (bat_buoc OR ma_nhom IS NOT NULL)
);

-- =====================================================================
-- 2. SINH VIÊN
-- =====================================================================

CREATE TABLE sinh_vien (
    ma_sv         VARCHAR(12)  PRIMARY KEY,
    ho_ten        VARCHAR(60)  NOT NULL,
    ma_ctdt       VARCHAR(15)  NOT NULL REFERENCES ctdt,   -- CTĐT chính
    ma_ctdt_2     VARCHAR(15)  REFERENCES ctdt,            -- CTĐT thứ hai (không xét HB)
    lop           VARCHAR(20),                             -- lớp hành chính
    ngay_nhap_hoc DATE         NOT NULL,
    trang_thai    VARCHAR(15)  NOT NULL DEFAULT 'dang_hoc'
                  CHECK (trang_thai IN ('dang_hoc', 'bao_luu', 'dinh_chi', 'thoi_hoc', 'tot_nghiep')),
    hb_dau_vao    VARCHAR(15)  CHECK (hb_dau_vao IN ('toan_khoa', 'nam_nhat', '5_trieu')),  -- diện HB HaUI
    -- Thông tin cá nhân: không đưa vào view chatbot
    ngay_sinh     DATE,
    email         VARCHAR(100),
    sdt           VARCHAR(15),
    dia_chi       VARCHAR(255),
    dan_toc       VARCHAR(30),
    quoc_tich     VARCHAR(50)
);

CREATE TABLE private.tai_khoan (
    ten_dn    VARCHAR(50)  PRIMARY KEY,
    ma_sv     VARCHAR(12)  UNIQUE REFERENCES core.sinh_vien,  -- NULL với tài khoản không phải SV
    mat_khau  VARCHAR(255) NOT NULL                           -- đã hash (bcrypt/argon2)
);

-- Quyết định học vụ: bảo lưu, trở lại, thôi học, tốt nghiệp
CREATE TABLE bien_dong (
    id        BIGSERIAL   PRIMARY KEY,
    ma_sv     VARCHAR(12) NOT NULL REFERENCES sinh_vien,
    loai      VARCHAR(15) NOT NULL
              CHECK (loai IN ('bao_luu', 'tro_lai', 'thoi_hoc', 'buoc_thoi_hoc', 'chuyen_nganh', 'tot_nghiep')),
    so_qd     VARCHAR(30),
    ngay_qd   DATE        NOT NULL,
    tu_ngay   DATE        NOT NULL,
    den_ngay  DATE
);

CREATE TABLE ky_luat (
    id            BIGSERIAL   PRIMARY KEY,
    ma_sv         VARCHAR(12) NOT NULL REFERENCES sinh_vien,
    hinh_thuc     VARCHAR(15) NOT NULL CHECK (hinh_thuc IN ('khien_trach', 'canh_cao', 'dinh_chi', 'buoc_thoi_hoc')),
    so_qd         VARCHAR(30) NOT NULL,
    ngay_qd       DATE        NOT NULL,
    het_hieu_luc  DATE,           -- khiển trách +3 tháng, cảnh cáo +6 tháng; buộc thôi học: NULL
    noi_dung      TEXT            -- không đưa vào view chatbot
);

-- Giải thưởng dùng xét HB
CREATE TABLE thanh_tich (
    id         BIGSERIAL    PRIMARY KEY,
    ma_sv      VARCHAR(12)  NOT NULL REFERENCES sinh_vien,
    nam_hoc    CHAR(9)      NOT NULL,
    loai       VARCHAR(15)  NOT NULL CHECK (loai IN ('nckh', 'tay_nghe', 'olympic', 'khac')),
    cap        VARCHAR(10)  NOT NULL CHECK (cap IN ('truong', 'tinh', 'quoc_gia', 'khu_vuc', 'quoc_te')),
    giai       VARCHAR(20)  NOT NULL,   -- 'nhat', 'nhi', 'ba', 'khuyen_khich'
    cuoc_thi   VARCHAR(200)
);

-- =====================================================================
-- 3. HỌC TẬP
-- =====================================================================

-- Quy đổi điểm chữ ↔ hệ 10 ↔ hệ 4
CREATE TABLE thang_diem (
    diem_chu  VARCHAR(2)   PRIMARY KEY,
    tu        NUMERIC(3,1),             -- ngưỡng hệ 10; NULL với I, X, R
    den       NUMERIC(3,1),
    diem_4    NUMERIC(2,1),             -- NULL: không quy đổi (P, I, X, R)
    dat       BOOLEAN,                  -- NULL: chưa có kết quả (I, X)
    tinh_tb   BOOLEAN      NOT NULL,
    mo_ta     VARCHAR(150) NOT NULL
);

-- Lớp học phần
CREATE TABLE lop_hp (
    ma_lop        VARCHAR(20)  PRIMARY KEY,
    ma_mon        VARCHAR(10)  NOT NULL REFERENCES mon,
    ma_hk         CHAR(5)      NOT NULL REFERENCES hoc_ky,
    theo_yeu_cau  BOOLEAN      NOT NULL DEFAULT false,
    si_so         SMALLINT,
    he_so         NUMERIC(2,1) NOT NULL DEFAULT 1.0   -- hệ số lớp khi tính học phí (lớp theo kế hoạch = 1,0)
);

CREATE TABLE dang_ky (
    ma_sv       VARCHAR(12) NOT NULL REFERENCES sinh_vien,
    ma_lop      VARCHAR(20) NOT NULL REFERENCES lop_hp,
    ngay        DATE        NOT NULL,
    loai        VARCHAR(10) NOT NULL CHECK (loai IN ('lan_dau', 'hoc_lai', 'cai_thien', 'hoc_doi')),
    trang_thai  VARCHAR(10) NOT NULL DEFAULT 'dang_ky' CHECK (trang_thai IN ('dang_ky', 'da_huy')),
    PRIMARY KEY (ma_sv, ma_lop)
);

-- Điểm học phần: mỗi dòng = một lần học. Môn học lại có nhiều dòng.
CREATE TABLE diem_hp (
    id          BIGSERIAL    PRIMARY KEY,
    ma_sv       VARCHAR(12)  NOT NULL REFERENCES sinh_vien,
    ma_mon      VARCHAR(10)  NOT NULL REFERENCES mon,
    ma_hk       CHAR(5)      NOT NULL REFERENCES hoc_ky,   -- HK thực học (có thể là HK phụ)
    ma_lop      VARCHAR(20)  REFERENCES lop_hp,            -- NULL với điểm R (miễn học)
    lan_hoc     SMALLINT     NOT NULL CHECK (lan_hoc >= 1),
    diem_qt     NUMERIC(3,1) CHECK (diem_qt  BETWEEN 0 AND 10),   -- điểm quá trình (TB trong kỳ)
    diem_thi    NUMERIC(3,1) CHECK (diem_thi BETWEEN 0 AND 10),
    diem_10     NUMERIC(3,1) CHECK (diem_10  BETWEEN 0 AND 10),   -- điểm học phần hệ 10
    diem_chu    VARCHAR(2)   REFERENCES thang_diem,
    chinh_thuc  BOOLEAN      NOT NULL DEFAULT false,  -- lần học được dùng tính TB tích lũy (điểm cao nhất)
    UNIQUE (ma_sv, ma_mon, lan_hoc)
);
CREATE UNIQUE INDEX uq_diem_chinh_thuc ON diem_hp (ma_sv, ma_mon) WHERE chinh_thuc;

-- Kết quả chính thức theo HK chính (đã gộp HK phụ)
CREATE TABLE ket_qua_hk (
    ma_sv        VARCHAR(12)  NOT NULL REFERENCES sinh_vien,
    ma_hk        CHAR(5)      NOT NULL REFERENCES hoc_ky,
    tc_dk        SMALLINT     NOT NULL,     -- TC đăng ký
    tc_dat       SMALLINT     NOT NULL,
    tc_truot     SMALLINT     NOT NULL,
    tb_hk        NUMERIC(3,2),              -- TB học kỳ, hệ 4
    tc_tich_luy  SMALLINT     NOT NULL,
    tb_tich_luy  NUMERIC(3,2),              -- TB tích lũy, hệ 4
    xep_loai     VARCHAR(12)  CHECK (xep_loai IN ('xuat_sac', 'gioi', 'kha', 'trung_binh', 'yeu', 'kem')),
    nam_thu      SMALLINT     CHECK (nam_thu BETWEEN 1 AND 4),   -- trình độ năm học; 4 = năm cuối
    canh_bao     BOOLEAN      NOT NULL DEFAULT false,
    PRIMARY KEY (ma_sv, ma_hk)
);

-- Điểm rèn luyện theo HK chính (đã áp trần do kỷ luật)
CREATE TABLE ren_luyen (
    ma_sv     VARCHAR(12) NOT NULL REFERENCES sinh_vien,
    ma_hk     CHAR(5)     NOT NULL REFERENCES hoc_ky,
    diem      SMALLINT    NOT NULL CHECK (diem BETWEEN 0 AND 100),
    xep_loai  VARCHAR(12) NOT NULL CHECK (xep_loai IN ('xuat_sac', 'tot', 'kha', 'trung_binh', 'yeu', 'kem')),
    PRIMARY KEY (ma_sv, ma_hk)
);

-- Điều kiện tốt nghiệp ngoài tín chỉ
CREATE TABLE dk_tot_nghiep (
    ma_sv     VARCHAR(12)  NOT NULL REFERENCES sinh_vien,
    loai      VARCHAR(10)  NOT NULL CHECK (loai IN ('ngoai_ngu', 'cntt', 'gdtc', 'gdqp')),
    dat       BOOLEAN      NOT NULL DEFAULT false,
    ngay_dat  DATE,
    ghi_chu   VARCHAR(200),             -- VD 'IELTS 5.5'
    PRIMARY KEY (ma_sv, loai)
);

-- =====================================================================
-- 4. HỌC BỔNG
-- =====================================================================

CREATE TABLE loai_hb (
    ma_loai  VARCHAR(15)  PRIMARY KEY,
    ten      VARCHAR(150) NOT NULL,
    nhom     VARCHAR(10)  NOT NULL CHECK (nhom IN ('haui', 'kkht', 'thac_si', 'tai_tro', 'ntb')),
    chu_ky   VARCHAR(10)  NOT NULL CHECK (chu_ky IN ('hoc_ky', 'nam_hoc')),
    van_ban  VARCHAR(150) NOT NULL
);

-- Mức HB theo năm học
CREATE TABLE muc_hb (
    ma_loai   VARCHAR(15)   NOT NULL REFERENCES loai_hb,
    nam_hoc   CHAR(9)       NOT NULL,
    xep_loai  VARCHAR(10)   NOT NULL DEFAULT 'chung' CHECK (xep_loai IN ('xuat_sac', 'gioi', 'kha', 'chung')),
    so_tien   NUMERIC(12,0),            -- mức tuyệt đối
    ty_le     NUMERIC(4,3),             -- hoặc tỷ lệ học phí (1.000 = 100%)
    ghi_chu   VARCHAR(200),
    PRIMARY KEY (ma_loai, nam_hoc, xep_loai),
    CHECK (so_tien IS NOT NULL OR ty_le IS NOT NULL)
);

-- HB sinh viên đã nhận
CREATE TABLE hoc_bong (
    id           BIGSERIAL     PRIMARY KEY,
    ma_sv        VARCHAR(12)   NOT NULL REFERENCES sinh_vien,
    ma_loai      VARCHAR(15)   NOT NULL REFERENCES loai_hb,
    ma_hk        CHAR(5)       REFERENCES hoc_ky,   -- HB xét theo học kỳ
    nam_hoc      CHAR(9),                           -- HB xét theo năm học
    xep_loai     VARCHAR(10)   CHECK (xep_loai IN ('xuat_sac', 'gioi', 'kha')),
    dt_ntb       VARCHAR(10),                       -- đối tượng HB Nguyễn Thanh Bình, VD '2.1.7'
    nha_tai_tro  VARCHAR(150),
    so_tien      NUMERIC(12,0) NOT NULL,
    so_qd        VARCHAR(30),
    ngay_qd      DATE,
    CHECK (ma_hk IS NOT NULL OR nam_hoc IS NOT NULL)
);

-- =====================================================================
-- 5. ĐỐI TƯỢNG & CHÍNH SÁCH
-- =====================================================================

-- Danh mục: ho_ngheo, khuyet_tat, mo_coi, dtts, ...
CREATE TABLE doi_tuong (
    ma_dt  VARCHAR(30)  PRIMARY KEY,
    ten    VARCHAR(200) NOT NULL
);

-- SV thuộc đối tượng nào, có thời hạn (hộ nghèo chỉ hiệu lực trong năm được công nhận)
CREATE TABLE sv_doi_tuong (
    ma_sv       VARCHAR(12) NOT NULL REFERENCES sinh_vien,
    ma_dt       VARCHAR(30) NOT NULL REFERENCES doi_tuong,
    tu_ngay     DATE        NOT NULL,
    den_ngay    DATE,
    trang_thai  VARCHAR(10) NOT NULL DEFAULT 'cho_duyet' CHECK (trang_thai IN ('cho_duyet', 'da_duyet', 'tu_choi')),
    PRIMARY KEY (ma_sv, ma_dt, tu_ngay)
);

-- Danh mục chính sách: miễn/giảm HP, hỗ trợ chi phí học tập, nội trú, ...
CREATE TABLE chinh_sach (
    ma_cs     VARCHAR(20)  PRIMARY KEY,
    ten       VARCHAR(200) NOT NULL,
    nhom      VARCHAR(15)  NOT NULL CHECK (nhom IN ('mien_hp', 'giam_hp', 'ho_tro_cp', 'noi_tru', 'ho_tro_ht', 'ho_tro_haui')),
    ty_le     NUMERIC(4,3),             -- 1.000, 0.700, ...
    co_so     VARCHAR(15)  NOT NULL CHECK (co_so IN ('muc_tran', 'luong_co_so', 'hoc_phi', 'khac')),  -- tính theo gì
    so_thang  SMALLINT,                 -- số tháng hưởng/năm
    can_cu    VARCHAR(150) NOT NULL
);

-- Chính sách SV được hưởng
CREATE TABLE sv_chinh_sach (
    id          BIGSERIAL   PRIMARY KEY,
    ma_sv       VARCHAR(12) NOT NULL REFERENCES sinh_vien,
    ma_cs       VARCHAR(20) NOT NULL REFERENCES chinh_sach,
    ma_dt       VARCHAR(30) REFERENCES doi_tuong,   -- đối tượng làm căn cứ
    tu_ngay     DATE        NOT NULL,
    den_ngay    DATE,
    so_qd       VARCHAR(30),
    trang_thai  VARCHAR(10) NOT NULL DEFAULT 'dang_huong' CHECK (trang_thai IN ('dang_huong', 'tam_dung', 'ket_thuc'))
);

-- Mức trần miễn giảm HP theo khối ngành, năm học (VND/SV/tháng)
CREATE TABLE muc_tran (
    ma_khoi    VARCHAR(20)   NOT NULL REFERENCES khoi_nganh,
    nam_hoc    CHAR(9)       NOT NULL,
    muc_thang  NUMERIC(12,0) NOT NULL,
    PRIMARY KEY (ma_khoi, nam_hoc)
);

-- Tham số theo thời gian: lương cơ sở, ...
CREATE TABLE tham_so (
    ma        VARCHAR(30)   NOT NULL,
    gia_tri   NUMERIC(14,2) NOT NULL,
    tu_ngay   DATE          NOT NULL,
    den_ngay  DATE,
    ghi_chu   VARCHAR(200),
    PRIMARY KEY (ma, tu_ngay)
);

-- =====================================================================
-- 6. HỌC PHÍ & TÀI CHÍNH
-- Học phí 1 lớp = n_hp × he_so_lop × don_gia
--   n_hp = tc_lt × 1,0 + tc_dac_thu × 1,5 + tc_th × 2,5
-- =====================================================================

-- Hệ số quy đổi tín chỉ học phí
CREATE TABLE he_so_tc (
    loai_tc  VARCHAR(10)  PRIMARY KEY CHECK (loai_tc IN ('lt', 'dac_thu', 'th')),
    he_so    NUMERIC(2,1) NOT NULL,
    mo_ta    VARCHAR(200) NOT NULL
);

-- Đơn giá 1 TC học phí theo năm học, bậc, khóa, loại CTĐT
CREATE TABLE don_gia (
    id         SERIAL        PRIMARY KEY,
    nam_hoc    CHAR(9)       NOT NULL,
    bac        VARCHAR(10)   NOT NULL CHECK (bac IN ('dai_hoc', 'ky_su', 'cao_dang')),
    khoa_tu    SMALLINT      NOT NULL,   -- áp dụng cho khóa [khoa_tu, khoa_den]
    khoa_den   SMALLINT      NOT NULL,
    hinh_thuc  VARCHAR(10)   NOT NULL CHECK (hinh_thuc IN ('chinh_quy', 'vlvh', 'tu_xa')),
    loai_ctdt  VARCHAR(10)   NOT NULL CHECK (loai_ctdt IN ('dai_tra', 'tieng_anh', 'tat_ca')),
    nhom_mon   VARCHAR(10)   NOT NULL DEFAULT 'tat_ca' CHECK (nhom_mon IN ('tat_ca', 'gdtc_gdqp')),
    don_gia    NUMERIC(12,0) NOT NULL,
    don_vi     VARCHAR(10)   NOT NULL CHECK (don_vi IN ('tc', 'thang', 'nam')),
    so_qd      VARCHAR(30)   NOT NULL
);

-- Khoản thu ngoài học phí: BHYT, BH thân thể, khám sức khỏe, ...
CREATE TABLE khoan_thu (
    ma_kt     VARCHAR(20)   PRIMARY KEY,
    ten       VARCHAR(150)  NOT NULL,
    nam_hoc   CHAR(9),
    bac       VARCHAR(10)   NOT NULL CHECK (bac IN ('dai_hoc', 'ky_su', 'cao_dang', 'lien_thong', 'tat_ca')),
    so_tien   NUMERIC(12,0) NOT NULL,
    chu_ky    VARCHAR(30)   NOT NULL,   -- '15 tháng', '4 năm học', 'khóa học', 'lượt'
    tu_ngay   DATE,
    den_ngay  DATE,
    ghi_chu   VARCHAR(300),
    so_qd     VARCHAR(30)
);

-- Khoản SV phải nộp. Dòng học phí lưu lại n_hp, he_so_lop, don_gia lúc tính.
CREATE TABLE phai_thu (
    id          BIGSERIAL     PRIMARY KEY,
    ma_sv       VARCHAR(12)   NOT NULL REFERENCES sinh_vien,
    ma_hk       CHAR(5)       NOT NULL REFERENCES hoc_ky,
    loai        VARCHAR(10)   NOT NULL CHECK (loai IN ('hoc_phi', 'khoan_thu', 'phi_phat', 'khac')),
    ma_lop      VARCHAR(20)   REFERENCES lop_hp,       -- với học phí
    ma_kt       VARCHAR(20)   REFERENCES khoan_thu,    -- với khoản thu
    n_hp        NUMERIC(5,2),                          -- số TC học phí
    he_so_lop   NUMERIC(2,1),
    don_gia     NUMERIC(12,0),
    so_tien     NUMERIC(12,0) NOT NULL CHECK (so_tien >= 0),
    han_nop     DATE,
    trang_thai  VARCHAR(10)   NOT NULL DEFAULT 'hieu_luc' CHECK (trang_thai IN ('hieu_luc', 'da_huy')),
    CHECK (loai <> 'hoc_phi' OR ma_lop IS NOT NULL)
);

-- Dòng tiền vào/ra tài khoản cá nhân của SV trên hệ thống ĐH điện tử
CREATE TABLE giao_dich (
    id           BIGSERIAL     PRIMARY KEY,
    ma_sv        VARCHAR(12)   NOT NULL REFERENCES sinh_vien,
    thoi_gian    TIMESTAMP     NOT NULL,
    loai         VARCHAR(15)   NOT NULL
                 CHECK (loai IN ('nap_tien', 'rut_tien', 'thanh_toan', 'hoan_tien', 'nhan_hb', 'nhan_mghp', 'nhan_ho_tro')),
    chieu        VARCHAR(3)    NOT NULL CHECK (chieu IN ('vao', 'ra')),
    so_tien      NUMERIC(12,0) NOT NULL CHECK (so_tien > 0),
    ma_phai_thu  BIGINT        REFERENCES phai_thu,   -- khi thanh toán
    ma_hb        BIGINT        REFERENCES hoc_bong,   -- khi nhận HB
    trang_thai   VARCHAR(12)   NOT NULL CHECK (trang_thai IN ('thanh_cong', 'that_bai', 'dang_xu_ly')),
    kenh         VARCHAR(20),                         -- 'ngan_hang', 'vi_dien_tu', 'he_thong'
    ghi_chu      VARCHAR(300)
);

-- =====================================================================
-- 7. GIẢNG DẠY (bổ sung ngoài thiết kế gốc)
-- Phục vụ trang Lịch học / Lịch thi / Thực tập và view v_lich_hoc, v_lich_thi, v_thuc_tap.
-- Nguồn chính khi chạy: SQLAlchemy model backend/src/chatbot_haui/db/models/ + Alembic.
-- DDL dưới đây sinh từ model, chép sang để bộ tài liệu này vẫn nạp được độc lập.
-- =====================================================================

-- giang_vien
CREATE TABLE giang_vien (
    ma_gv VARCHAR(10) NOT NULL, 
    ho_ten VARCHAR(60) NOT NULL, 
    ma_khoa VARCHAR(10) NOT NULL, 
    hoc_vi VARCHAR(5), 
    email VARCHAR(100), 
    sdt VARCHAR(15), 
    PRIMARY KEY (ma_gv), 
    CONSTRAINT ck_giang_vien_hoc_vi CHECK (hoc_vi IN ('ths', 'ts', 'pgs', 'gs')), 
    FOREIGN KEY(ma_khoa) REFERENCES khoa (ma_khoa)
);

-- Lịch học hằng tuần của lớp học phần. thu: 2..7 = thứ Hai..thứ Bảy, 8 = Chủ nhật.
CREATE TABLE lich_hoc (
    id BIGSERIAL NOT NULL, 
    ma_lop VARCHAR(20) NOT NULL, 
    thu SMALLINT NOT NULL, 
    tiet_bd SMALLINT NOT NULL, 
    so_tiet SMALLINT NOT NULL, 
    phong VARCHAR(20), 
    tuan_bd SMALLINT, 
    tuan_kt SMALLINT, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_lich_hoc_thu CHECK (thu BETWEEN 2 AND 8), 
    CONSTRAINT ck_lich_hoc_tiet_bd CHECK (tiet_bd BETWEEN 1 AND 15), 
    CONSTRAINT ck_lich_hoc_so_tiet CHECK (so_tiet BETWEEN 1 AND 6), 
    CONSTRAINT ck_lich_hoc_tuan CHECK (tuan_kt IS NULL OR tuan_bd IS NULL OR tuan_kt >= tuan_bd), 
    CONSTRAINT uq_lich_hoc_ca UNIQUE (ma_lop, thu, tiet_bd), 
    FOREIGN KEY(ma_lop) REFERENCES lop_hp (ma_lop)
);
CREATE INDEX ix_lich_hoc_lop ON lich_hoc (ma_lop);

-- Ca thi của lớp học phần. lan_thi = 2 là thi lại.
CREATE TABLE lich_thi (
    id BIGSERIAL NOT NULL, 
    ma_lop VARCHAR(20) NOT NULL, 
    lan_thi SMALLINT DEFAULT '1' NOT NULL, 
    thoi_gian TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    so_phut SMALLINT NOT NULL, 
    hinh_thuc VARCHAR(15) NOT NULL, 
    phong VARCHAR(20), 
    PRIMARY KEY (id), 
    CONSTRAINT ck_lich_thi_lan CHECK (lan_thi IN (1, 2)), 
    CONSTRAINT ck_lich_thi_so_phut CHECK (so_phut BETWEEN 15 AND 300), 
    CONSTRAINT ck_lich_thi_hinh_thuc CHECK (hinh_thuc IN ('tu_luan', 'trac_nghiem', 'van_dap', 'thuc_hanh', 'tieu_luan')), 
    CONSTRAINT uq_lich_thi_lop_lan UNIQUE (ma_lop, lan_thi), 
    FOREIGN KEY(ma_lop) REFERENCES lop_hp (ma_lop)
);
CREATE INDEX ix_lich_thi_lop ON lich_thi (ma_lop);

-- SV trong ca thi: số báo danh, vị trí, điều kiện dự thi.
CREATE TABLE lich_thi_sv (
    ma_lich_thi BIGINT NOT NULL, 
    ma_sv VARCHAR(12) NOT NULL, 
    so_bd SMALLINT NOT NULL, 
    vi_tri VARCHAR(10), 
    du_dieu_kien BOOLEAN DEFAULT 'true' NOT NULL, 
    ly_do VARCHAR(200), 
    PRIMARY KEY (ma_lich_thi, ma_sv), 
    CONSTRAINT ck_lich_thi_sv_so_bd CHECK (so_bd > 0), 
    CONSTRAINT ck_lich_thi_sv_ly_do CHECK (du_dieu_kien OR ly_do IS NOT NULL), 
    FOREIGN KEY(ma_lich_thi) REFERENCES lich_thi (id), 
    FOREIGN KEY(ma_sv) REFERENCES sinh_vien (ma_sv)
);
CREATE INDEX ix_lich_thi_sv_sv ON lich_thi_sv (ma_sv);

-- doanh_nghiep
CREATE TABLE doanh_nghiep (
    ma_dn VARCHAR(10) NOT NULL, 
    ten VARCHAR(150) NOT NULL, 
    dia_chi VARCHAR(255), 
    linh_vuc VARCHAR(100), 
    email VARCHAR(100), 
    sdt VARCHAR(15), 
    PRIMARY KEY (ma_dn)
);

-- Kỳ thực tập của SV tại doanh nghiệp, gắn với học phần thực tập trong CTĐT.
CREATE TABLE thuc_tap (
    id BIGSERIAL NOT NULL, 
    ma_sv VARCHAR(12) NOT NULL, 
    ma_dn VARCHAR(10) NOT NULL, 
    ma_hk CHAR(5) NOT NULL, 
    ma_mon VARCHAR(10), 
    ma_gv VARCHAR(10), 
    vi_tri VARCHAR(100), 
    tu_ngay DATE NOT NULL, 
    den_ngay DATE, 
    trang_thai VARCHAR(15) DEFAULT 'dang_thuc_tap' NOT NULL, 
    diem NUMERIC(3, 1), 
    PRIMARY KEY (id), 
    CONSTRAINT ck_thuc_tap_trang_thai CHECK (trang_thai IN ('dang_thuc_tap', 'hoan_thanh', 'huy')), 
    CONSTRAINT ck_thuc_tap_diem CHECK (diem BETWEEN 0 AND 10), 
    CONSTRAINT ck_thuc_tap_ngay CHECK (den_ngay IS NULL OR den_ngay >= tu_ngay), 
    FOREIGN KEY(ma_sv) REFERENCES sinh_vien (ma_sv), 
    FOREIGN KEY(ma_dn) REFERENCES doanh_nghiep (ma_dn), 
    FOREIGN KEY(ma_hk) REFERENCES hoc_ky (ma_hk), 
    FOREIGN KEY(ma_mon) REFERENCES mon (ma_mon), 
    FOREIGN KEY(ma_gv) REFERENCES giang_vien (ma_gv)
);
CREATE INDEX ix_thuc_tap_sv ON thuc_tap (ma_sv);

-- Giảng viên phụ trách và phòng học mặc định của lớp học phần
ALTER TABLE lop_hp ADD COLUMN ma_gv VARCHAR(10) REFERENCES giang_vien;
ALTER TABLE lop_hp ADD COLUMN phong VARCHAR(20);

-- =====================================================================
-- INDEX
-- =====================================================================
CREATE INDEX ix_diem_hp_sv_hk   ON diem_hp (ma_sv, ma_hk);
CREATE INDEX ix_dang_ky_lop     ON dang_ky (ma_lop);
CREATE INDEX ix_lop_hp_hk       ON lop_hp (ma_hk);
CREATE INDEX ix_phai_thu_sv_hk  ON phai_thu (ma_sv, ma_hk);
CREATE INDEX ix_giao_dich_sv    ON giao_dich (ma_sv, thoi_gian);
CREATE INDEX ix_hoc_bong_sv     ON hoc_bong (ma_sv);
CREATE INDEX ix_ky_luat_sv      ON ky_luat (ma_sv);
CREATE INDEX ix_sv_cs_sv        ON sv_chinh_sach (ma_sv);
