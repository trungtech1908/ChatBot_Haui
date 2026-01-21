USE CSDLDoAnCN;

-- =========================
-- 1. VIEW: SINH VIÊN
-- =========================
CREATE OR REPLACE VIEW v_sinhVien
SQL SECURITY INVOKER
AS
SELECT *
FROM sinhVien
WHERE maSV = SUBSTRING_INDEX(USER(), '@', 1);

-- =========================
-- 2. VIEW: TÀI CHÍNH
-- =========================
CREATE OR REPLACE VIEW v_taiChinh
SQL SECURITY INVOKER
AS
SELECT *
FROM taiChinh
WHERE maSV = SUBSTRING_INDEX(USER(), '@', 1);

-- =========================
-- 3. VIEW: ĐỐI TƯỢNG
-- =========================
CREATE OR REPLACE VIEW v_doiTuong
SQL SECURITY INVOKER
AS
SELECT *
FROM doiTuong
WHERE maSV = SUBSTRING_INDEX(USER(), '@', 1);

-- =========================
-- 4. VIEW: ĐIỀU KIỆN TỐT NGHIỆP
-- =========================
CREATE OR REPLACE VIEW v_dieuKienTotNghiep
SQL SECURITY INVOKER
AS
SELECT *
FROM dieuKienTotNghiep
WHERE maSV = SUBSTRING_INDEX(USER(), '@', 1);

-- =========================
-- 5. VIEW: TÀI KHOẢN
-- =========================
CREATE OR REPLACE VIEW v_taiKhoan
SQL SECURITY INVOKER
AS
SELECT *
FROM taiKhoan
WHERE maSV = SUBSTRING_INDEX(USER(), '@', 1);

-- =========================
-- 6. VIEW: KẾT QUẢ MÔN HỌC
-- =========================
CREATE OR REPLACE VIEW v_ketQuaMonHoc
SQL SECURITY INVOKER
AS
SELECT *
FROM ketQuaMonHoc
WHERE maSV = SUBSTRING_INDEX(USER(), '@', 1);

-- =========================
-- 7. VIEW: GIAO DỊCH
-- =========================
CREATE OR REPLACE VIEW v_giaoDich
SQL SECURITY INVOKER
AS
SELECT *
FROM giaoDich
WHERE maSV = SUBSTRING_INDEX(USER(), '@', 1);

-- =========================
-- 8. VIEW: SINH VIÊN - LỚP HỌC
-- =========================
CREATE OR REPLACE VIEW v_sinhVienLopHoc
SQL SECURITY INVOKER
AS
SELECT *
FROM sinhVienLopHoc
WHERE maSV = SUBSTRING_INDEX(USER(), '@', 1);

-- =========================
-- 9. VIEW: LỊCH THI SINH VIÊN
-- =========================
CREATE OR REPLACE VIEW v_lichThiSV
SQL SECURITY INVOKER
AS
SELECT *
FROM lichThiSV
WHERE maSV = SUBSTRING_INDEX(USER(), '@', 1);

-- =========================
-- 10. VIEW: THỰC TẬP
-- =========================
CREATE OR REPLACE VIEW v_thucTap
SQL SECURITY INVOKER
AS
SELECT *
FROM thucTap
WHERE maSV = SUBSTRING_INDEX(USER(), '@', 1);

-- =========================
-- 11. USER MẪU (SV001)
-- =========================
CREATE USER IF NOT EXISTS 'SV001'@'%' IDENTIFIED BY 'pwd';

REVOKE ALL PRIVILEGES ON *.* FROM 'SV001'@'%';

GRANT SELECT ON CSDLDoAnCN.v_sinhVien TO 'SV001'@'%';
GRANT SELECT ON CSDLDoAnCN.v_taiChinh TO 'SV001'@'%';
GRANT SELECT ON CSDLDoAnCN.v_doiTuong TO 'SV001'@'%';
GRANT SELECT ON CSDLDoAnCN.v_dieuKienTotNghiep TO 'SV001'@'%';
GRANT SELECT ON CSDLDoAnCN.v_taiKhoan TO 'SV001'@'%';
GRANT SELECT ON CSDLDoAnCN.v_ketQuaMonHoc TO 'SV001'@'%';
GRANT SELECT ON CSDLDoAnCN.v_giaoDich TO 'SV001'@'%';
GRANT SELECT ON CSDLDoAnCN.v_sinhVienLopHoc TO 'SV001'@'%';
GRANT SELECT ON CSDLDoAnCN.v_lichThiSV TO 'SV001'@'%';
GRANT SELECT ON CSDLDoAnCN.v_thucTap TO 'SV001'@'%';

-- Bảng không chứa dữ liệu riêng sinh viên
GRANT SELECT ON CSDLDoAnCN.monHoc TO 'SV001'@'%';
GRANT SELECT ON CSDLDoAnCN.lopHoc TO 'SV001'@'%';
GRANT SELECT ON CSDLDoAnCN.khoa TO 'SV001'@'%';
GRANT SELECT ON CSDLDoAnCN.giangVien TO 'SV001'@'%';
GRANT SELECT ON CSDLDoAnCN.ctdt TO 'SV001'@'%';

FLUSH PRIVILEGES;
