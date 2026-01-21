/* =========================================================
   FILE: agent_secure_views.sql
   Mục tiêu:
   - Agent được sinh SQL tự do
   - Chỉ truy cập dữ liệu của sinh viên hiện tại
   - Không tạo nhiều user / nhiều bảng / nhiều view theo SV
   ========================================================= */

USE CSDLDoAnCN;

/* =========================================================
   1. FUNCTION: lấy maSV theo SESSION
   ========================================================= */
DELIMITER //

DROP FUNCTION IF EXISTS current_maSV;
CREATE FUNCTION current_maSV()
RETURNS CHAR(10)
DETERMINISTIC
BEGIN
    RETURN @current_maSV;
END//

DELIMITER ;


/* =========================================================
   2. VIEW: các view chỉ nhìn thấy dữ liệu của 1 sinh viên
   ========================================================= */

DROP VIEW IF EXISTS v_sinhVien;
CREATE VIEW v_sinhVien AS
SELECT *
FROM sinhVien
WHERE maSV = current_maSV();

DROP VIEW IF EXISTS v_taiChinh;
CREATE VIEW v_taiChinh AS
SELECT *
FROM taiChinh
WHERE maSV = current_maSV();

DROP VIEW IF EXISTS v_doiTuong;
CREATE VIEW v_doiTuong AS
SELECT *
FROM doiTuong
WHERE maSV = current_maSV();

DROP VIEW IF EXISTS v_dieuKienTotNghiep;
CREATE VIEW v_dieuKienTotNghiep AS
SELECT *
FROM dieuKienTotNghiep
WHERE maSV = current_maSV();

DROP VIEW IF EXISTS v_ketQuaMonHoc;
CREATE VIEW v_ketQuaMonHoc AS
SELECT *
FROM ketQuaMonHoc
WHERE maSV = current_maSV();

DROP VIEW IF EXISTS v_giaoDich;
CREATE VIEW v_giaoDich AS
SELECT *
FROM giaoDich
WHERE maSV = current_maSV();

DROP VIEW IF EXISTS v_sinhVienLopHoc;
CREATE VIEW v_sinhVienLopHoc AS
SELECT *
FROM sinhVienLopHoc
WHERE maSV = current_maSV();

DROP VIEW IF EXISTS v_lichThiSV;
CREATE VIEW v_lichThiSV AS
SELECT *
FROM lichThiSV
WHERE maSV = current_maSV();

DROP VIEW IF EXISTS v_thucTap;
CREATE VIEW v_thucTap AS
SELECT *
FROM thucTap
WHERE maSV = current_maSV();

/* =========================================================
   3. DB USER: user runtime cho Agent
   ========================================================= */

DROP USER IF EXISTS 'agent_runtime'@'%';
CREATE USER 'agent_runtime'@'%' IDENTIFIED BY 'strong_pwd';

REVOKE ALL PRIVILEGES ON *.* FROM 'agent_runtime'@'%';

/* --- Chỉ cho SELECT VIEW --- */
GRANT SELECT ON CSDLDoAnCN.v_sinhVien TO 'agent_runtime'@'%';
GRANT SELECT ON CSDLDoAnCN.v_taiChinh TO 'agent_runtime'@'%';
GRANT SELECT ON CSDLDoAnCN.v_doiTuong TO 'agent_runtime'@'%';
GRANT SELECT ON CSDLDoAnCN.v_dieuKienTotNghiep TO 'agent_runtime'@'%';
GRANT SELECT ON CSDLDoAnCN.v_ketQuaMonHoc TO 'agent_runtime'@'%';
GRANT SELECT ON CSDLDoAnCN.v_giaoDich TO 'agent_runtime'@'%';
GRANT SELECT ON CSDLDoAnCN.v_sinhVienLopHoc TO 'agent_runtime'@'%';
GRANT SELECT ON CSDLDoAnCN.v_lichThiSV TO 'agent_runtime'@'%';
GRANT SELECT ON CSDLDoAnCN.v_thucTap TO 'agent_runtime'@'%';

/* --- Bảng public, không chứa dữ liệu riêng SV --- */
GRANT SELECT ON CSDLDoAnCN.monHoc TO 'agent_runtime'@'%';
GRANT SELECT ON CSDLDoAnCN.lopHoc TO 'agent_runtime'@'%';
GRANT SELECT ON CSDLDoAnCN.khoa TO 'agent_runtime'@'%';
GRANT SELECT ON CSDLDoAnCN.giangVien TO 'agent_runtime'@'%';
GRANT SELECT ON CSDLDoAnCN.ctdt TO 'agent_runtime'@'%';

FLUSH PRIVILEGES;

/* =========================================================
   4. GHI CHÚ VẬN HÀNH (KHÔNG PHẢI CODE)
   =========================================================
   Backend phải chạy:
     SET @current_maSV = 'SVxxx';
   trước khi thực thi SQL do Agent sinh.

   Agent:
   - Không biết @current_maSV
   - Không thấy bảng gốc
   - Chỉ thấy view
   ========================================================= */
