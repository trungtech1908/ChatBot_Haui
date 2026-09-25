"""Sinh dữ liệu mẫu cho CSDL hỏi đáp quy chế HaUI.

Dữ liệu chốt tại 31/08/2026 (hết năm học 2025-2026).
Điểm, kết quả học kỳ, rèn luyện, học bổng được TÍNH theo quy chế, không random độc lập:
  - điểm học phần = (quá trình + 2 × thi) / 3, làm tròn 1 chữ số; thi = 0 → điểm liệt
  - TB học kỳ / tích lũy, xếp loại, trình độ năm, cảnh báo: QCĐT Điều 10–11
  - xét HB KKHT: QĐ 725 Điều 4, 7; HB HaUI: Điều 5–6; HB NTB: QĐ 279
  - học phí = n_hp × hệ số lớp × đơn giá (chỉ năm học 2025-2026, năm duy nhất có đơn giá trong văn bản)
Mức tiền HB KKHT, NTB, tài trợ là MINH HỌA (văn bản không công bố).

Bổ sung ngoài bản gốc (dùng RNG riêng, chạy sau cùng để KHÔNG làm lệch dữ liệu cũ):
  - giảng viên, lịch học, lịch thi, số báo danh, doanh nghiệp, thực tập
  - mật khẩu tài khoản = mã SV, hash argon2 thật (bản gốc là chuỗi giả, không đăng nhập được)

Chạy từ backend/: uv run --no-sync python scripts/gen_sample_data.py
"""
import hashlib
import random
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, timedelta
from pathlib import Path

from argon2 import PasswordHasher
from argon2.low_level import Type, hash_secret

SEED = 2026
SV_MOI_NHOM = 3                  # số SV mỗi (ngành × khóa)
OUT = Path(__file__).resolve().parents[1] / "assets" / "seed" / "04_sample_data.sql"
LUONG_CO_SO = 2340000            # NĐ 73/2024/NĐ-CP, từ 01/07/2024

random.seed(SEED)

# ---------------------------------------------------------------------
# Danh mục
# ---------------------------------------------------------------------
KHOA = [
    ("CNTT", "Trường Công nghệ Thông tin và Truyền thông"),
    ("COKHI", "Trường Cơ khí - Ô tô"),
    ("DIEN", "Trường Điện - Điện tử"),
    ("KINHTE", "Trường Kinh tế"),
    ("NGOAINGU", "Khoa Ngoại ngữ"),
]
# ma_nganh, ten, ma_khoa, ma_khoi, khoi_ntb, prefix mã SV, mã lớp
NGANH = [
    ("7480201", "Công nghệ thông tin", "CNTT", "DH_CNTT_KT", "ky_thuat", "1", "CNTT"),
    ("7510205", "Công nghệ kỹ thuật ô tô", "COKHI", "DH_CNTT_KT", "ky_thuat", "2", "OTO"),
    ("7510301", "Công nghệ kỹ thuật điện, điện tử", "DIEN", "DH_CNTT_KT", "ky_thuat", "3", "DIEN"),
    ("7340301", "Kế toán", "KINHTE", "DH_KD_QL_PL", "xa_hoi", "4", "KT"),
    ("7220201", "Ngôn ngữ Anh", "NGOAINGU", "DH_NHAN_VAN_XH", "xa_hoi", "5", "NNA"),
]
NIEN_KHOA = [("DH-K17", 17, 2022), ("DH-K18", 18, 2023), ("DH-K19", 19, 2024), ("DH-K20", 20, 2025)]

# Môn: ma, ten, so_tc, tc_lt, tc_dac_thu, tc_th, loai, tinh_tb, xet_hb
M = {}
def mon(ma, ten, tc, lt=None, dt=0, th=0, loai="thuong", tinh_tb=True, xet_hb=True):
    lt = tc - dt - th if lt is None else lt
    M[ma] = (ma, ten, tc, lt, dt, th, loai, tinh_tb, xet_hb)
    return ma

# Đại cương dùng chung
G = dict(
    triet=mon("LP6010", "Triết học Mác - Lênin", 3),
    ktct=mon("LP6011", "Kinh tế chính trị Mác - Lênin", 2),
    cnxh=mon("LP6012", "Chủ nghĩa xã hội khoa học", 2),
    lsd=mon("LP6013", "Lịch sử Đảng Cộng sản Việt Nam", 2),
    tthcm=mon("LP6014", "Tư tưởng Hồ Chí Minh", 2),
    phapluat=mon("BS6010", "Pháp luật đại cương", 2),
    cntt=mon("IT6000", "Kỹ năng sử dụng công nghệ thông tin", 2, lt=1, th=1, loai="cntt", xet_hb=False),
    ta1=mon("FL6001", "Tiếng Anh cơ sở 1", 3, dt=3, loai="ngoai_ngu", xet_hb=False),
    ta2=mon("FL6002", "Tiếng Anh cơ sở 2", 3, dt=3, loai="ngoai_ngu", xet_hb=False),
    ta3=mon("FL6003", "Tiếng Anh cơ sở 3", 3, dt=3, loai="ngoai_ngu", xet_hb=False),
    tq1=mon("FL6011", "Tiếng Trung 1", 3, dt=3, loai="ngoai_ngu", xet_hb=False),
    tq2=mon("FL6012", "Tiếng Trung 2", 3, dt=3, loai="ngoai_ngu", xet_hb=False),
    tq3=mon("FL6013", "Tiếng Trung 3", 3, dt=3, loai="ngoai_ngu", xet_hb=False),
    gdtc1=mon("PE6001", "Giáo dục thể chất 1", 1, loai="gdtc", tinh_tb=False, xet_hb=False),
    gdtc2=mon("PE6002", "Giáo dục thể chất 2", 1, loai="gdtc", tinh_tb=False, xet_hb=False),
    gdtc3=mon("PE6003", "Giáo dục thể chất 3", 1, loai="gdtc", tinh_tb=False, xet_hb=False),
    gdtc4=mon("PE6004", "Giáo dục thể chất 4", 1, loai="gdtc", tinh_tb=False, xet_hb=False),
    gdqp=mon("DC6001", "Giáo dục quốc phòng và an ninh", 8, loai="gdqp", tinh_tb=False, xet_hb=False),
    giaitich=mon("BS6001", "Giải tích", 3),
    daiso=mon("BS6002", "Đại số tuyến tính", 3),
    xstk=mon("BS6004", "Xác suất thống kê", 3),
    vatly=mon("BS6005", "Vật lý đại cương", 3, th=1),
    toancc=mon("BS6006", "Toán cao cấp", 3),
    vhvn=mon("BS6011", "Cơ sở văn hóa Việt Nam", 2),
)

def dai_cuong(ngoai_ngu):
    nn = [G["ta1"], G["ta2"], G["ta3"]] if ngoai_ngu == "anh" else [G["tq1"], G["tq2"], G["tq3"]]
    return {
        1: [G["triet"], G["phapluat"], G["cntt"], nn[0], G["gdtc1"]],
        2: [G["ktct"], nn[1], G["gdtc2"], G["gdqp"]],
        3: [G["cnxh"], nn[2], G["gdtc3"]],
        4: [G["lsd"], G["gdtc4"]],
        5: [G["tthcm"]],
    }

# Chuyên ngành: {hk_thu: [môn]}, nhóm tự chọn (chọn 2/3, học HK6 và HK7)
CT = {}
CT["7480201"] = ({
    1: [G["giaitich"], G["daiso"], mon("IT6002", "Nhập môn công nghệ thông tin", 2), mon("IT6003", "Lập trình C", 3, th=1)],
    2: [mon("IT6004", "Toán rời rạc", 3), mon("IT6005", "Cấu trúc dữ liệu và giải thuật", 3, th=1), mon("IT6006", "Kiến trúc máy tính", 3), G["xstk"]],
    3: [mon("IT6007", "Lập trình hướng đối tượng", 3, th=1), mon("IT6008", "Cơ sở dữ liệu", 3, th=1), mon("IT6009", "Hệ điều hành", 3), mon("IT6010", "Mạng máy tính", 3, th=1)],
    4: [mon("IT6011", "Phân tích và thiết kế hệ thống", 3), mon("IT6012", "Lập trình Web", 3, th=1), mon("IT6013", "Trí tuệ nhân tạo", 3), mon("IT6014", "Công nghệ phần mềm", 3), mon("IT6015", "Đồ án cơ sở ngành", 2, dt=2)],
    5: [mon("IT6016", "Học máy", 3, th=1), mon("IT6017", "An toàn bảo mật thông tin", 3), mon("IT6018", "Phát triển ứng dụng di động", 3, th=1), mon("IT6027", "Hệ quản trị cơ sở dữ liệu", 3, th=1)],
    6: [mon("IT6022", "Kiểm thử phần mềm", 3, th=1), mon("IT6023", "Quản lý dự án công nghệ thông tin", 2), mon("IT6028", "Đồ án chuyên ngành", 3, dt=3), mon("IT6029", "Xử lý ngôn ngữ tự nhiên", 3)],
    7: [mon("IT6024", "Thực tập doanh nghiệp", 4, dt=4, loai="thuc_tap"), mon("IT6030", "Chuyên đề công nghệ mới", 3)],
    8: [mon("IT6025", "Đồ án tốt nghiệp", 8, dt=8, loai="do_an")],
}, ("Nhóm tự chọn chuyên sâu", [mon("IT6019", "Điện toán đám mây", 3), mon("IT6020", "Xử lý ảnh", 3), mon("IT6021", "Dữ liệu lớn", 3)]))

CT["7510205"] = ({
    1: [G["giaitich"], G["daiso"], mon("ME6001", "Vẽ kỹ thuật", 3, th=1), mon("AT6000", "Nhập môn công nghệ ô tô", 2)],
    2: [G["vatly"], mon("ME6002", "Cơ học lý thuyết", 3), mon("ME6003", "Vật liệu cơ khí", 2), mon("ME6007", "Hình họa", 2)],
    3: [mon("ME6004", "Sức bền vật liệu", 3), mon("ME6005", "Nguyên lý máy", 3), mon("EE6001", "Kỹ thuật điện - điện tử", 3, th=1), mon("ME6008", "Nhiệt động học kỹ thuật", 3)],
    4: [mon("AT6001", "Nguyên lý động cơ đốt trong", 3), mon("AT6002", "Lý thuyết ô tô", 3), mon("ME6006", "Dung sai và đo lường", 2, th=1), mon("AT6003", "Thực hành động cơ", 2, lt=0, th=2), mon("ME6009", "Chi tiết máy", 3)],
    5: [mon("AT6004", "Kết cấu ô tô", 3), mon("AT6005", "Hệ thống điện - điện tử ô tô", 3, th=1), mon("AT6006", "Đồ án kết cấu ô tô", 2, dt=2), mon("AT6015", "Thực hành gầm ô tô", 2, lt=0, th=2), mon("AT6016", "Động lực học ô tô", 3)],
    6: [mon("AT6007", "Chẩn đoán và sửa chữa ô tô", 3, lt=1, th=2), mon("AT6008", "Hệ thống điều khiển động cơ", 3), mon("AT6017", "Công nghệ bảo dưỡng ô tô", 3, th=1), mon("AT6018", "Tiếng Anh chuyên ngành ô tô", 2)],
    7: [mon("AT6012", "Kiểm định ô tô", 3, th=1), mon("AT6013", "Thực tập doanh nghiệp", 4, dt=4, loai="thuc_tap")],
    8: [mon("AT6014", "Đồ án tốt nghiệp", 8, dt=8, loai="do_an")],
}, ("Nhóm tự chọn ô tô", [mon("AT6009", "Ô tô điện và hybrid", 3), mon("AT6010", "Công nghệ khung vỏ ô tô", 3), mon("AT6011", "Thiết kế ô tô trên máy tính", 3, th=1)]))

CT["7510301"] = ({
    1: [G["giaitich"], G["daiso"], mon("EE6002", "Nhập môn kỹ thuật điện", 2), mon("EE6022", "Vật liệu điện", 2)],
    2: [G["vatly"], mon("EE6003", "Lý thuyết mạch 1", 3), mon("EE6004", "Vẽ điện", 2, th=1), G["xstk"]],
    3: [mon("EE6005", "Lý thuyết mạch 2", 3), mon("EE6006", "Điện tử tương tự", 3, th=1), mon("EE6007", "Đo lường điện", 3, th=1), mon("EE6023", "Trường điện từ", 3)],
    4: [mon("EE6008", "Máy điện", 3, th=1), mon("EE6009", "Điện tử số", 3, th=1), mon("EE6010", "Kỹ thuật vi xử lý", 3, th=1), mon("EE6024", "Lý thuyết điều khiển tự động", 3)],
    5: [mon("EE6011", "Điện tử công suất", 3), mon("EE6012", "Cung cấp điện", 3), mon("EE6013", "Đồ án cung cấp điện", 2, dt=2), mon("EE6025", "Khí cụ điện", 3, th=1), mon("EE6026", "Thực hành điện cơ bản", 2, lt=0, th=2)],
    6: [mon("EE6014", "Truyền động điện", 3), mon("EE6015", "Điều khiển logic khả trình PLC", 3, lt=1, th=2), mon("EE6027", "Hệ thống điện", 3), mon("EE6028", "Tiếng Anh chuyên ngành điện", 2)],
    7: [mon("EE6019", "An toàn điện", 2), mon("EE6020", "Thực tập doanh nghiệp", 4, dt=4, loai="thuc_tap")],
    8: [mon("EE6021", "Đồ án tốt nghiệp", 8, dt=8, loai="do_an")],
}, ("Nhóm tự chọn điện", [mon("EE6016", "Năng lượng tái tạo", 3), mon("EE6017", "Hệ thống SCADA", 3, th=1), mon("EE6018", "Điều khiển thông minh", 3)]))

CT["7340301"] = ({
    1: [G["toancc"], mon("BA6001", "Kinh tế vi mô", 3), mon("BA6005", "Quản trị học", 3), mon("BA6006", "Tin học ứng dụng trong kinh tế", 3, th=1)],
    2: [mon("BA6003", "Kinh tế vĩ mô", 3), mon("AC6001", "Nguyên lý kế toán", 3), G["xstk"], mon("BA6007", "Luật kinh tế", 2)],
    3: [mon("AC6002", "Tài chính tiền tệ", 3), mon("BA6004", "Marketing căn bản", 3), mon("AC6003", "Kế toán tài chính 1", 3), mon("BA6008", "Thống kê kinh tế", 3)],
    4: [mon("AC6004", "Kế toán tài chính 2", 3), mon("AC6005", "Thuế", 3), mon("AC6006", "Kế toán quản trị", 3), mon("BA6009", "Kinh tế lượng", 3)],
    5: [mon("AC6007", "Kiểm toán căn bản", 3), mon("AC6008", "Kế toán máy", 3, lt=1, th=2), mon("AC6009", "Phân tích báo cáo tài chính", 3), mon("AC6018", "Tài chính công", 3)],
    6: [mon("AC6010", "Kế toán tài chính 3", 3), mon("AC6011", "Tài chính doanh nghiệp", 3), mon("AC6019", "Kế toán thuế", 3), mon("AC6020", "Tiếng Anh chuyên ngành kế toán", 2)],
    7: [mon("AC6015", "Kiểm toán báo cáo tài chính", 3), mon("AC6016", "Thực tập doanh nghiệp", 4, dt=4, loai="thuc_tap")],
    8: [mon("AC6017", "Khóa luận tốt nghiệp", 8, dt=8, loai="do_an")],
}, ("Nhóm tự chọn kế toán", [mon("AC6012", "Kế toán công", 3), mon("AC6013", "Kế toán ngân hàng", 3), mon("AC6014", "Hệ thống thông tin kế toán", 3)]))

CT["7220201"] = ({
    1: [mon("EN6001", "Nghe 1", 2, dt=2), mon("EN6002", "Nói 1", 2, dt=2), mon("EN6003", "Đọc 1", 2, dt=2), mon("EN6004", "Viết 1", 2, dt=2), G["vhvn"]],
    2: [mon("EN6005", "Nghe 2", 2, dt=2), mon("EN6006", "Nói 2", 2, dt=2), mon("EN6007", "Đọc 2", 2, dt=2), mon("EN6008", "Viết 2", 2, dt=2), mon("EN6009", "Ngữ âm - âm vị học", 2), mon("BS6012", "Dẫn luận ngôn ngữ học", 2)],
    3: [mon("EN6010", "Nghe 3", 2, dt=2), mon("EN6011", "Nói 3", 2, dt=2), mon("EN6012", "Đọc 3", 2, dt=2), mon("EN6013", "Viết 3", 2, dt=2), mon("EN6014", "Ngữ pháp tiếng Anh", 3), mon("EN6029", "Ngữ nghĩa học", 2)],
    4: [mon("EN6015", "Từ vựng học", 2), mon("EN6016", "Văn hóa Anh - Mỹ", 3), mon("EN6017", "Lý thuyết dịch", 3), mon("EN6018", "Tiếng Anh thương mại", 3), mon("EN6030", "Nghe 4", 2, dt=2), mon("EN6031", "Nói 4", 2, dt=2)],
    5: [mon("EN6019", "Biên dịch 1", 3), mon("EN6020", "Phiên dịch 1", 3), mon("EN6021", "Văn học Anh", 3), mon("EN6032", "Ngôn ngữ học đối chiếu", 3), mon("EN6033", "Viết học thuật", 2, dt=2)],
    6: [mon("EN6022", "Biên dịch 2", 3), mon("EN6023", "Phiên dịch 2", 3), mon("EN6034", "Văn học Mỹ", 3), mon("EN6035", "Tiếng Anh văn phòng", 3)],
    7: [mon("EN6027", "Thực tập doanh nghiệp", 4, dt=4, loai="thuc_tap"), mon("EN6036", "Kỹ năng thuyết trình tiếng Anh", 2)],
    8: [mon("EN6028", "Khóa luận tốt nghiệp", 8, dt=8, loai="do_an")],
}, ("Nhóm tự chọn ngôn ngữ", [mon("EN6024", "Tiếng Anh du lịch", 3), mon("EN6025", "Phương pháp giảng dạy tiếng Anh", 3), mon("EN6026", "Tiếng Anh kỹ thuật", 3)]))

def ke_hoach(ma_nganh):
    """{hk_thu: [ma_mon]} gồm đại cương + chuyên ngành; tự chọn tách riêng."""
    chuyen, (ten_nhom, tu_chon) = CT[ma_nganh]
    dc = dai_cuong("trung" if ma_nganh == "7220201" else "anh")
    kh = {k: list(dc.get(k, [])) + list(chuyen.get(k, [])) for k in range(1, 9)}
    return kh, ten_nhom, tu_chon

# ---------------------------------------------------------------------
# Tiện ích
# ---------------------------------------------------------------------
def r1(x):  return float(Decimal(str(x)).quantize(Decimal("0.1"), ROUND_HALF_UP))
def r2(x):  return float(Decimal(str(x)).quantize(Decimal("0.01"), ROUND_HALF_UP))
def r05(x): return max(0.0, min(10.0, round(x * 2) / 2))

THANG = [("A", 8.5, 4.0), ("B+", 7.7, 3.5), ("B", 7.0, 3.0), ("C+", 6.2, 2.5),
         ("C", 5.5, 2.0), ("D+", 4.7, 1.5), ("D", 4.0, 1.0), ("F", 0.0, 0.0)]
D4 = {c: d4 for c, _, d4 in THANG}

def diem_chu(d10, tinh_tb):
    if not tinh_tb:
        return "P" if d10 >= 5.0 else "F"
    return next(c for c, nguong, _ in THANG if d10 >= nguong)

def dat(chu):  return chu in ("A", "B+", "B", "C+", "C", "D+", "D", "P", "R")
def tinh_tb_chu(chu): return chu in D4

def xep_loai_hl(tb):
    for nguong, xl in [(3.6, "xuat_sac"), (3.2, "gioi"), (2.5, "kha"), (2.0, "trung_binh"), (1.0, "yeu")]:
        if tb >= nguong:
            return xl
    return "kem"

def xep_loai_rl(d):
    for nguong, xl in [(90, "xuat_sac"), (80, "tot"), (65, "kha"), (50, "trung_binh"), (35, "yeu")]:
        if d >= nguong:
            return xl
    return "kem"

def q(v):
    if v is None:          return "NULL"
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, (int, float)): return repr(v)
    if isinstance(v, datetime): return f"'{v.isoformat(sep=' ')}'"
    if isinstance(v, date): return f"'{v.isoformat()}'"
    return "'" + str(v).replace("'", "''") + "'"

ROWS = {}
def ins(bang, **kv):
    ROWS.setdefault(bang, []).append(kv)

# ---------------------------------------------------------------------
# Học kỳ: 20221 → 20253
# ---------------------------------------------------------------------
HK = {}           # ma_hk -> (nam_hoc, loai, ten, ma_hk_chinh, bd, kt)
HK_CHINH = []
for y in range(2022, 2026):
    nh = f"{y}-{y + 1}"
    HK[f"{y}1"] = (nh, "chinh", f"Học kỳ 1 năm học {nh}", f"{y}1", date(y, 9, 5), date(y + 1, 1, 14))
    HK[f"{y}2"] = (nh, "chinh", f"Học kỳ 2 năm học {nh}", f"{y}2", date(y + 1, 2, 17), date(y + 1, 6, 28))
    HK[f"{y}3"] = (nh, "phu", f"Học kỳ phụ hè năm học {nh}", f"{y}2", date(y + 1, 7, 6), date(y + 1, 8, 16))
    HK_CHINH += [f"{y}1", f"{y}2"]
for ma, (nh, loai, ten, chinh, bd, kt) in HK.items():
    ins("hoc_ky", ma_hk=ma, nam_hoc=nh, loai=loai, ten=ten, ma_hk_chinh=chinh, ngay_bd=bd, ngay_kt=kt)

def nam_hoc_cua(ma_hk): return HK[ma_hk][0]

# ---------------------------------------------------------------------
# Tên người, địa chỉ
# ---------------------------------------------------------------------
HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Vũ", "Đỗ", "Bùi", "Đặng", "Ngô", "Dương", "Lý", "Đinh", "Tạ", "Phan", "Trịnh"]
DEM_NAM = ["Văn", "Đức", "Minh", "Quang", "Hữu", "Tuấn", "Thành", "Công", "Mạnh", "Hoàng"]
DEM_NU = ["Thị", "Thu", "Ngọc", "Thanh", "Phương", "Minh", "Khánh", "Thùy", "Hồng", "Mai"]
TEN_NAM = ["An", "Bình", "Cường", "Dũng", "Đạt", "Hiếu", "Hùng", "Huy", "Khánh", "Long", "Nam", "Phúc", "Quân", "Sơn", "Thắng", "Trung", "Tùng", "Việt"]
TEN_NU = ["Anh", "Chi", "Dung", "Giang", "Hà", "Hằng", "Hương", "Lan", "Linh", "Mai", "Ngân", "Nhung", "Phương", "Quỳnh", "Thảo", "Trang", "Vân", "Yến"]
DIA_CHI = ["Huyện Đông Anh, TP Hà Nội", "Huyện Thạch Thất, TP Hà Nội", "Quận Bắc Từ Liêm, TP Hà Nội", "Huyện Yên Lạc, Tỉnh Vĩnh Phúc",
           "Huyện Thanh Sơn, Tỉnh Phú Thọ", "TP Bắc Ninh, Tỉnh Bắc Ninh", "Huyện Kim Sơn, Tỉnh Ninh Bình", "Huyện Hải Hậu, Tỉnh Nam Định",
           "Huyện Thái Thụy, Tỉnh Thái Bình", "Huyện Tiên Lãng, TP Hải Phòng", "Huyện Lục Ngạn, Tỉnh Bắc Giang", "Huyện Nghĩa Đàn, Tỉnh Nghệ An",
           "Huyện Thiệu Hóa, Tỉnh Thanh Hóa", "TP Hòa Bình, Tỉnh Hòa Bình", "Huyện Kim Bảng, Tỉnh Hà Nam", "Huyện Văn Giang, Tỉnh Hưng Yên"]
KHONG_DAU = str.maketrans("àáảãạăằắẳẵặâầấẩẫậđèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ",
                          "aaaaaaaaaaaaaaaaadeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyy")
DUNG_TEN = set()

def ten_nguoi():
    while True:
        nu = random.random() < 0.45
        ten = f"{random.choice(HO)} {random.choice(DEM_NU if nu else DEM_NAM)} {random.choice(TEN_NU if nu else TEN_NAM)}"
        if ten not in DUNG_TEN:
            DUNG_TEN.add(ten)
            return ten

# ---------------------------------------------------------------------
# Hồ sơ đặc biệt (ép tình huống để có đủ trường hợp hỏi đáp)
# key: (ma_nganh, ma_nk, stt)
# ---------------------------------------------------------------------
DAC_BIET = {
    ("7480201", "DH-K20", 1): dict(nang_luc=8.9, hb_dau_vao="toan_khoa"),
    ("7510301", "DH-K20", 1): dict(nang_luc=8.2, hb_dau_vao="nam_nhat"),
    ("7510205", "DH-K20", 2): dict(nang_luc=7.6, hb_dau_vao="5_trieu"),
    ("7480201", "DH-K19", 2): dict(nang_luc=7.9, khuyet_tat=True),
    ("7340301", "DH-K20", 2): dict(nang_luc=7.4, dan_toc="Tày", ho_ngheo=True, dia_chi="Huyện Na Rì, Tỉnh Bắc Kạn"),
    ("7220201", "DH-K18", 1): dict(nang_luc=8.6, can_ngheo=True),
    ("7510301", "DH-K19", 3): dict(nang_luc=7.0, mo_coi=True),
    ("7510205", "DH-K18", 3): dict(nang_luc=6.8, cha_tnld=True),
    ("7340301", "DH-K19", 3): dict(nang_luc=7.8, ky_luat=("khien_trach", date(2025, 3, 12))),
    ("7480201", "DH-K18", 2): dict(nang_luc=7.2, ky_luat=("canh_cao", date(2024, 11, 6))),
    ("7510301", "DH-K18", 2): dict(nang_luc=7.1, bao_luu=("20232", "20242")),
    ("7340301", "DH-K19", 2): dict(nang_luc=3.1, yeu=True),
    ("7480201", "DH-K18", 1): dict(nang_luc=9.0, thanh_tich=("olympic", "quoc_gia", "ba", "Olympic Tin học sinh viên Việt Nam", "2024-2025"), tai_tro=True),
    ("7510205", "DH-K19", 1): dict(nang_luc=8.3, thanh_tich=("nckh", "truong", "nhat", "Hội nghị NCKH sinh viên cấp trường", "2024-2025")),
    ("7220201", "DH-K20", 2): dict(nang_luc=7.5, dan_toc="Mường", dia_chi="Huyện Tân Lạc, Tỉnh Hòa Bình"),
    ("7480201", "DH-K17", 3): dict(nang_luc=5.4),
    ("7220201", "DH-K19", 3): dict(nang_luc=7.7, hoan_thi=True),
}

# ---------------------------------------------------------------------
# Tạo khoa, ngành, niên khóa, CTĐT, môn
# ---------------------------------------------------------------------
for ma, ten in KHOA:
    ins("khoa", ma_khoa=ma, ten=ten)
for ma, ten, khoa, khoi, ntb, _, _ in NGANH:
    ins("nganh", ma_nganh=ma, ten=ten, ma_khoa=khoa, ma_khoi=khoi, khoi_ntb=ntb)
for ma, so, nam in NIEN_KHOA:
    ins("nien_khoa", ma_nk=ma, bac="dai_hoc", so_khoa=so, nam_nhap_hoc=nam)
for m in M.values():
    ins("mon", ma_mon=m[0], ten=m[1], so_tc=m[2], tc_lt=m[3], tc_dac_thu=m[4], tc_th=m[5], loai=m[6], tinh_tb=m[7], xet_hb=m[8])

CTDT = {}    # ma_ctdt -> dict
for ma_nganh, ten_nganh, *_ in NGANH:
    kh, ten_nhom, tu_chon = ke_hoach(ma_nganh)
    for ma_nk, so_khoa, nam in NIEN_KHOA:
        loai_list = ["dai_tra", "tieng_anh"] if (ma_nganh == "7480201" and ma_nk == "DH-K20") else ["dai_tra"]
        for loai in loai_list:
            ma_ctdt = f"{ma_nganh}-K{so_khoa}" + ("-TA" if loai == "tieng_anh" else "")
            so_tc = sum(M[x][2] for k in kh for x in kh[k] if M[x][6] not in ("gdtc", "gdqp")) + 6
            ins("ctdt", ma_ctdt=ma_ctdt, ten=f"{ten_nganh}{' (tiếng Anh)' if loai == 'tieng_anh' else ''} K{so_khoa}",
                ma_nganh=ma_nganh, ma_nk=ma_nk, hinh_thuc="chinh_quy", loai=loai, so_tc=so_tc, so_hk=8)
            ma_nhom = f"{next(n[6] for n in NGANH if n[0] == ma_nganh)}K{so_khoa}{'TA' if loai == 'tieng_anh' else ''}-TC"
            ins("nhom_tu_chon", ma_nhom=ma_nhom, ma_ctdt=ma_ctdt, ten=ten_nhom, so_tc=6)
            for k, ds in kh.items():
                for x in ds:
                    ins("ctdt_mon", ma_ctdt=ma_ctdt, ma_mon=x, bat_buoc=True, ma_nhom=None, hk_thu=k)
            for x in tu_chon:
                ins("ctdt_mon", ma_ctdt=ma_ctdt, ma_mon=x, bat_buoc=False, ma_nhom=ma_nhom, hk_thu=6)
            CTDT[ma_ctdt] = dict(nganh=ma_nganh, nk=ma_nk, so_khoa=so_khoa, nam=nam, loai=loai, so_tc=so_tc, kh=kh, tu_chon=tu_chon)

# ---------------------------------------------------------------------
# Lớp học phần
# ---------------------------------------------------------------------
LOP = {}   # (ma_hk, ma_mon, nhom_lop) -> ma_lop

def he_so_lop(ma_mon, si_so):
    _, _, tc, lt, dt, th, loai, *_ = M[ma_mon]
    if loai in ("do_an", "thuc_tap"):
        return 1.0
    bac = 0 if si_so < 5 else 1 if si_so < 10 else 2 if si_so < 20 else 3 if si_so < 40 else 4
    if th == tc or loai == "ngoai_ngu":
        return [3, 2, 1.5, 1, 1][bac]
    return [3, 3, 2, 1.5, 1][bac]

def lop(ma_hk, ma_mon, nhom_lop):
    key = (ma_hk, ma_mon, nhom_lop)
    if key not in LOP:
        phu = HK[ma_hk][1] == "phu"
        si_so = random.randint(6, 38) if phu else random.randint(42, 68)
        stt = sum(1 for k in LOP if k[0] == ma_hk and k[1] == ma_mon) + 1
        ma_lop = f"{ma_hk}{ma_mon}{stt:02d}"
        LOP[key] = ma_lop
        ins("lop_hp", ma_lop=ma_lop, ma_mon=ma_mon, ma_hk=ma_hk, theo_yeu_cau=phu, si_so=si_so,
            he_so=he_so_lop(ma_mon, si_so) if phu else 1.0)
    return LOP[key]

# ---------------------------------------------------------------------
# Sinh viên & quá trình học
# ---------------------------------------------------------------------
SV = []
for ma_ctdt, c in CTDT.items():
    so_sv = 3 if c["loai"] == "dai_tra" else 2
    for stt in range(1, so_sv + 1):
        cfg = DAC_BIET.get((c["nganh"], c["nk"], stt), {}) if c["loai"] == "dai_tra" else {}
        prefix = next(n[5] for n in NGANH if n[0] == c["nganh"])
        ma_sv = f"{c['nam']}6{prefix}{random.randint(1000, 9999)}"
        while any(x["ma_sv"] == ma_sv for x in SV):
            ma_sv = f"{c['nam']}6{prefix}{random.randint(1000, 9999)}"
        ho_ten = ten_nguoi()
        ten_ks = ho_ten.lower().translate(KHONG_DAU).split()
        SV.append(dict(
            ma_sv=ma_sv, ho_ten=ho_ten, ctdt=ma_ctdt, c=c, cfg=cfg,
            nang_luc=cfg.get("nang_luc", max(4.2, min(9.2, random.gauss(7.0, 0.9)))),
            ky_luat_tinh=random.gauss(83, 6),
            lop=f"{next(n[6] for n in NGANH if n[0] == c['nganh'])}{stt % 2 + 1:02d}-K{c['so_khoa']}{'TA' if c['loai'] == 'tieng_anh' else ''}",
            ngay_sinh=date(c["nam"] - 18, 1, 1) + timedelta(days=random.randint(0, 364)),
            email=f"{ten_ks[-1]}{''.join(w[0] for w in ten_ks[:-1])}{random.randint(10, 99)}@gmail.com",
            sdt=random.choice(["03", "08", "09"]) + str(random.randint(10000000, 99999999)),
            dia_chi=cfg.get("dia_chi", f"Thôn {random.randint(1, 12)}, {random.choice(DIA_CHI)}"),
            dan_toc=cfg.get("dan_toc", "Kinh"),
            diem=[], trang_thai="dang_hoc", ket_qua={}, ren_luyen={},
        ))

DO_KHO = {ma: random.gauss(0, 0.45) for ma in M}
DIEM_ROWS = []        # (sv, ma_mon, ma_hk, ma_lop, lan, qt, thi, d10, chu, loai_dk)
DANG_KY = []

def cham(sv, ma_mon, lan):
    nl = sv["nang_luc"] + DO_KHO[ma_mon] + (0.5 if lan > 1 else 0)
    base = random.gauss(nl, 0.85)
    qt = r05(base + random.gauss(0.4, 0.6))
    thi = 0.0 if random.random() < 0.01 else r05(base + random.gauss(-0.2, 0.9))
    d10 = 0.0 if thi == 0 else r1((qt + 2 * thi) / 3)
    return qt, thi, d10

def hoc(sv, ma_mon, ma_hk, lan, loai_dk, nhom_lop):
    ma_lop = lop(ma_hk, ma_mon, nhom_lop)
    DANG_KY.append((sv, ma_lop, ma_hk, loai_dk))
    qt, thi, d10 = cham(sv, ma_mon, lan)
    chu = diem_chu(d10, M[ma_mon][7])
    rec = dict(ma_mon=ma_mon, ma_hk=ma_hk, ma_lop=ma_lop, lan=lan, qt=qt, thi=thi, d10=d10, chu=chu, loai_dk=loai_dk)
    sv["diem"].append(rec)
    return rec

def ky_luat_trong(sv, bd, kt):
    kl = sv["cfg"].get("ky_luat")
    if not kl:
        return None
    hinh_thuc, ngay = kl
    het = ngay + timedelta(days=92 if hinh_thuc == "khien_trach" else 183)
    return hinh_thuc if ngay <= kt and het >= bd else None

def lan_hoc(sv, ma_mon):
    return sum(1 for d in sv["diem"] if d["ma_mon"] == ma_mon) + 1

def da_dat(sv, ma_mon):
    return any(d["ma_mon"] == ma_mon and dat(d["chu"]) for d in sv["diem"])

for sv in SV:
    c = sv["c"]
    bao_luu = sv["cfg"].get("bao_luu")
    tu_chon = random.sample(c["tu_chon"], 2)
    hk_thu = 0
    no_mon = []
    canh_bao_lien_tiep = 0
    for ma_hk in HK_CHINH:
        if int(ma_hk[:4]) < c["nam"] or sv["trang_thai"] != "dang_hoc":
            continue
        if bao_luu and bao_luu[0] <= ma_hk <= bao_luu[1]:
            continue
        hk_thu += 1
        if hk_thu > 8:
            break
        nhom_lop = sv["ctdt"]
        ds = list(c["kh"][hk_thu]) + ([tu_chon[0]] if hk_thu == 6 else []) + ([tu_chon[1]] if hk_thu == 7 else [])
        for ma_mon in ds:
            rec = hoc(sv, ma_mon, ma_hk, 1, "lan_dau", nhom_lop)
            if sv["cfg"].get("hoan_thi") and ma_hk == "20252" and ma_mon == ds[0]:
                rec.update(thi=None, d10=None, chu="I")
        # học lại trong HK chính: 1 môn nợ cũ
        for ma_mon in list(no_mon):
            if not da_dat(sv, ma_mon) and random.random() < 0.5:
                hoc(sv, ma_mon, ma_hk, lan_hoc(sv, ma_mon), "hoc_lai", "chung")
        # sorted: thứ tự duyệt set chuỗi phụ thuộc PYTHONHASHSEED → không sort thì mỗi lần chạy ra dữ liệu khác
        no_mon = [x for x in sorted(set(no_mon + [d["ma_mon"] for d in sv["diem"] if d["ma_hk"] == ma_hk and d["chu"] == "F"]))
                  if not da_dat(sv, x)]
        # học kỳ phụ hè sau HK2: học lại môn nợ, cải thiện môn D/D+
        if ma_hk.endswith("2"):
            he = ma_hk[:4] + "3"
            for ma_mon in list(no_mon):
                if random.random() < 0.7:
                    hoc(sv, ma_mon, he, lan_hoc(sv, ma_mon), "hoc_lai", "chung")
            for d in [d for d in sv["diem"] if HK[d["ma_hk"]][3] == ma_hk and d["chu"] in ("D", "D+") and d["lan"] == 1]:
                if random.random() < 0.3 and not any(x["ma_mon"] == d["ma_mon"] and x["lan"] > 1 for x in sv["diem"]):
                    hoc(sv, d["ma_mon"], he, lan_hoc(sv, d["ma_mon"]), "cai_thien", "chung")
            no_mon = [x for x in no_mon if not da_dat(sv, x)]

        # ---- kết quả chính thức của HK chính (đã gộp HK phụ) ----
        trong_ky = [d for d in sv["diem"] if HK[d["ma_hk"]][3] == ma_hk]
        tc_dk = sum(M[d["ma_mon"]][2] for d in trong_ky)
        tc_dat = sum(M[d["ma_mon"]][2] for d in trong_ky if dat(d["chu"]))
        tc_truot = sum(M[d["ma_mon"]][2] for d in trong_ky if d["chu"] == "F")
        tot_nhat = {}
        for d in trong_ky:
            if M[d["ma_mon"]][7] and tinh_tb_chu(d["chu"]):
                if d["ma_mon"] not in tot_nhat or D4[d["chu"]] > D4[tot_nhat[d["ma_mon"]]["chu"]]:
                    tot_nhat[d["ma_mon"]] = d
        tc_tb = sum(M[x][2] for x in tot_nhat)
        tb_hk = r2(sum(D4[d["chu"]] * M[x][2] for x, d in tot_nhat.items()) / tc_tb) if tc_tb else None
        den_nay = [d for d in sv["diem"] if HK[d["ma_hk"]][3] <= ma_hk and dat(d["chu"]) and M[d["ma_mon"]][6] not in ("gdtc", "gdqp")]
        chinh = {}
        for d in den_nay:
            if d["ma_mon"] not in chinh or (d["d10"] or 0) > (chinh[d["ma_mon"]]["d10"] or 0):
                chinh[d["ma_mon"]] = d
        tc_tl = sum(M[x][2] for x in chinh)
        tl_tb = {x: d for x, d in chinh.items() if M[x][7] and tinh_tb_chu(d["chu"])}
        tb_tl = r2(sum(D4[d["chu"]] * M[x][2] for x, d in tl_tb.items()) / sum(M[x][2] for x in tl_tb)) if tl_tb else None
        ty = tc_tl / c["so_tc"]
        nam_thu = 1 if ty <= 0.25 else 2 if ty <= 0.5 else 3 if ty <= 0.75 else 4
        canh_bao = (tb_hk is not None and tb_hk < (0.8 if hk_thu == 1 else 1.0)) or \
                   (tb_tl is not None and tb_tl < [1.2, 1.4, 1.6, 1.8][nam_thu - 1])
        sv["ket_qua"][ma_hk] = dict(tc_dk=tc_dk, tc_dat=tc_dat, tc_truot=tc_truot, tb_hk=tb_hk, tc_tl=tc_tl, tb_tl=tb_tl,
                                    xep_loai=xep_loai_hl(tb_hk) if tb_hk is not None else None, nam_thu=nam_thu,
                                    canh_bao=canh_bao, hk_thu=hk_thu)
        # ---- rèn luyện (đã áp trần kỷ luật) ----
        drl = int(max(38, min(98, round(random.gauss(sv["ky_luat_tinh"], 5)))))
        kl = ky_luat_trong(sv, HK[ma_hk][4], HK[ma_hk][5])
        if kl == "khien_trach": drl = min(drl, 79)
        if kl == "canh_cao":    drl = min(drl, 64)
        sv["ren_luyen"][ma_hk] = drl
        # ---- buộc thôi học: cảnh báo 2 lần liên tiếp ----
        canh_bao_lien_tiep = canh_bao_lien_tiep + 1 if canh_bao else 0
        if canh_bao_lien_tiep >= 2:
            sv["trang_thai"] = "thoi_hoc"
            sv["buoc_thoi_hoc"] = HK[ma_hk][5] + timedelta(days=45)

# ---------------------------------------------------------------------
# Điểm chính thức, tốt nghiệp
# ---------------------------------------------------------------------
for sv in SV:
    best = {}
    for d in sv["diem"]:
        if d["chu"] == "I":
            continue
        b = best.get(d["ma_mon"])
        if b is None or (d["d10"], d["lan"]) > (b["d10"], b["lan"]):
            best[d["ma_mon"]] = d
    for d in sv["diem"]:
        d["chinh_thuc"] = best.get(d["ma_mon"]) is d
    sv["dat_mon"] = {x for x, d in best.items() if dat(d["chu"])}

for sv in SV:
    c = sv["c"]
    can = {x for k in c["kh"] for x in c["kh"][k]}
    sv["dk_tn"] = dict(
        gdtc=all(x in sv["dat_mon"] for x in (G["gdtc1"], G["gdtc2"], G["gdtc3"], G["gdtc4"])),
        gdqp=G["gdqp"] in sv["dat_mon"],
        cntt=G["cntt"] in sv["dat_mon"],
        ngoai_ngu=(c["nam"] <= 2023 and random.random() < (0.85 if c["nam"] == 2022 else 0.4)) or sv["nang_luc"] > 8.8,
    )
    kq_cuoi = sv["ket_qua"].get("20252")
    if (c["nam"] == 2022 and sv["trang_thai"] == "dang_hoc" and can <= sv["dat_mon"]
            and len(set(t for t in c["tu_chon"]) & sv["dat_mon"]) >= 2 and all(sv["dk_tn"].values())
            and kq_cuoi and kq_cuoi["tb_tl"] and kq_cuoi["tb_tl"] >= 2.0):
        sv["trang_thai"] = "tot_nghiep"

# ---------------------------------------------------------------------
# Học bổng
# ---------------------------------------------------------------------
HB = []   # dict(sv, ma_loai, ma_hk, nam_hoc, xep_loai, dt_ntb, nha_tai_tro, so_tien, so_qd, ngay_qd)
MUC_KKHT = {"xuat_sac": 6200000, "gioi": 5500000, "kha": 4800000}     # MINH HỌA
MUC_NTB = 3000000                                                      # MINH HỌA

def xet_kkht(sv, ma_hk):
    kq = sv["ket_qua"].get(ma_hk)
    if not kq:
        return None
    trong_ky = [d for d in sv["diem"] if HK[d["ma_hk"]][3] == ma_hk and tinh_tb_chu(d["chu"])]
    xet = [d for d in trong_ky if d["lan"] == 1 and M[d["ma_mon"]][8] and M[d["ma_mon"]][7]]
    tc = sum(M[d["ma_mon"]][2] for d in xet)
    if not tc:
        return None
    tb = r2(sum(D4[d["chu"]] * M[d["ma_mon"]][2] for d in xet) / tc)
    tb10 = r2(sum(d["d10"] * M[d["ma_mon"]][2] for d in xet) / tc)
    rl = xep_loai_rl(sv["ren_luyen"][ma_hk])
    hk_thu_lich = (int(ma_hk[:4]) - sv["c"]["nam"]) * 2 + int(ma_hk[4])
    ok = (tb >= 2.5 and rl in ("xuat_sac", "tot") and min(D4[d["chu"]] for d in trong_ky) >= 2.0
          and tc >= (7 if hk_thu_lich == 8 else 15) and hk_thu_lich <= 8
          and not ky_luat_trong(sv, HK[ma_hk][4], HK[ma_hk][5]))
    xl = ("xuat_sac" if tb >= 3.6 and rl == "xuat_sac" else "gioi" if tb >= 3.2 else "kha") if ok else None
    return dict(ok=ok, tb=tb, tb10=tb10, tc=tc, rl=rl, xl=xl)

qd_so = iter(range(1402, 9999, 37))

# HB HaUI (K20)
def hoc_phi_lan_dau(sv, ma_hk):   # tính sau khi có đơn giá, dùng lambda trễ
    return sum(p["so_tien"] for p in PHAI_THU if p["sv"] is sv and p["ma_hk"] == ma_hk and p["loai"] == "hoc_phi"
               and p["loai_dk"] == "lan_dau" and M[p["ma_mon"]][6] not in ("ngoai_ngu", "cntt"))

HAUI_PENDING = []
for sv in SV:
    hb = sv["cfg"].get("hb_dau_vao")
    if hb in ("toan_khoa", "nam_nhat"):
        for ma_hk in ("20251", "20252"):
            if ma_hk == "20252":
                x = xet_kkht(sv, "20251")
                if not (x and x["tb"] >= 2.5 and x["rl"] in ("xuat_sac", "tot") and x["tc"] >= 15):
                    continue
            HAUI_PENDING.append((sv, "HAUI_TOAN_KHOA" if hb == "toan_khoa" else "HAUI_NAM_NHAT", ma_hk))
    if hb == "5_trieu":
        HB.append(dict(sv=sv, ma_loai="HAUI_5TR", ma_hk=None, nam_hoc="2025-2026", xep_loai=None, dt_ntb=None,
                       nha_tai_tro=None, so_tien=5000000, so_qd=f"{next(qd_so)}/QĐ-ĐHCN", ngay_qd=date(2025, 10, 20)))

# KKHT: mỗi (CTĐT, HK) cấp tối đa 1 suất cho SV đủ điều kiện có kết quả cao nhất (quỹ có hạn)
haui_hk = {(sv["ma_sv"], hk) for sv, _, hk in HAUI_PENDING}
for ma_ctdt in CTDT:
    for ma_hk in HK_CHINH:
        ung_vien = []
        for sv in SV:
            if sv["ctdt"] != ma_ctdt or (sv["ma_sv"], ma_hk) in haui_hk:
                continue
            x = xet_kkht(sv, ma_hk)
            if x and x["ok"]:
                ung_vien.append((["kha", "gioi", "xuat_sac"].index(x["xl"]), x["tb10"], sv, x))
        for _, _, sv, x in sorted(ung_vien, key=lambda t: (t[0], t[1]), reverse=True)[:1]:
            HB.append(dict(sv=sv, ma_loai="KKHT", ma_hk=ma_hk, nam_hoc=None, xep_loai=x["xl"], dt_ntb=None, nha_tai_tro=None,
                           so_tien=MUC_KKHT[x["xl"]], so_qd=f"{next(qd_so)}/QĐ-ĐHCN", ngay_qd=HK[ma_hk][5] + timedelta(days=60)))

# NTB năm học 2024-2025
def tb_nam(sv, nam):
    ds = [d for d in sv["diem"] if HK[d["ma_hk"]][0] == nam and M[d["ma_mon"]][7] and tinh_tb_chu(d["chu"])]
    tc = sum(M[d["ma_mon"]][2] for d in ds)
    return (r2(sum(D4[d["chu"]] * M[d["ma_mon"]][2] for d in ds) / tc) if tc else 0, tc, min([D4[d["chu"]] for d in ds] or [0]))

for sv in SV:
    cfg = sv["cfg"]
    dt = "2.1.2" if cfg.get("khuyet_tat") else "2.1.3" if cfg.get("mo_coi") else "2.1.5" if cfg.get("can_ngheo") else None
    if not dt:
        continue
    tb, tc, thap = tb_nam(sv, "2024-2025")
    rls = [xep_loai_rl(sv["ren_luyen"][h]) for h in ("20241", "20242") if h in sv["ren_luyen"]]
    if dt in ("2.1.2", "2.1.3"):
        ok = tb >= 2.0 and all(r in ("xuat_sac", "tot", "kha") for r in rls) and tc >= (25 if dt == "2.1.2" else 30) and thap >= 1.0
    else:
        ok = tb >= 3.2 and all(r in ("xuat_sac", "tot") for r in rls) and tc >= 30 and thap >= 1.0
    if ok:
        HB.append(dict(sv=sv, ma_loai="NTB", ma_hk=None, nam_hoc="2024-2025", xep_loai=None, dt_ntb=dt, nha_tai_tro=None,
                       so_tien=int(MUC_NTB * (1.2 if dt in ("2.1.2", "2.1.3") else 1.0)),
                       so_qd=f"{next(qd_so)}/QĐ-ĐHCN", ngay_qd=date(2025, 11, 18)))

for sv in SV:
    if sv["cfg"].get("tai_tro"):
        HB.append(dict(sv=sv, ma_loai="TAI_TRO", ma_hk=None, nam_hoc="2025-2026", xep_loai=None, dt_ntb=None,
                       nha_tai_tro="Công ty TNHH Công nghệ đối tác (minh họa)", so_tien=10000000,
                       so_qd=f"{next(qd_so)}/QĐ-ĐHCN", ngay_qd=date(2025, 12, 5)))

# ---------------------------------------------------------------------
# Học phí & khoản thu năm học 2025-2026
# ---------------------------------------------------------------------
def don_gia(sv, ma_mon):
    c = sv["c"]
    if c["so_khoa"] <= 18: return 495000
    if c["so_khoa"] == 19: return 550000
    if c["loai"] == "tieng_anh" and M[ma_mon][6] not in ("gdtc", "gdqp"): return 1000000
    return 700000

HAN = {"20251": date(2025, 10, 15), "20252": date(2026, 3, 16), "20253": date(2026, 7, 13)}
LOP_INFO = {}
for r in ROWS["lop_hp"]:
    LOP_INFO[r["ma_lop"]] = r
PHAI_THU = []
for sv, ma_lop, ma_hk, loai_dk in DANG_KY:
    if HK[ma_hk][0] != "2025-2026":
        continue
    ma_mon = LOP_INFO[ma_lop]["ma_mon"]
    _, _, tc, lt, dt, th, *_ = M[ma_mon]
    n_hp = r2(lt * 1.0 + dt * 1.5 + th * 2.5)
    hs = LOP_INFO[ma_lop]["he_so"]
    dg = don_gia(sv, ma_mon)
    PHAI_THU.append(dict(sv=sv, ma_hk=ma_hk, loai="hoc_phi", ma_lop=ma_lop, ma_kt=None, n_hp=n_hp, he_so_lop=hs,
                         don_gia=dg, so_tien=int(round(n_hp * hs * dg)), han_nop=HAN[ma_hk], ma_mon=ma_mon, loai_dk=loai_dk))

KT_K20 = [("2526_BHYT15_DH", 789750), ("2526_BHTT_DH", 325000), ("2526_KSK_DH", 120000), ("2526_QKH_DH", 20000)]
for sv in SV:
    if not any(p["sv"] is sv for p in PHAI_THU):
        continue
    if sv["c"]["nam"] == 2025:
        ds = KT_K20 + ([("2526_BHLD_DH", 400000)] if sv["c"]["nganh"] in ("7510205", "7510301") else [])
        for ma_kt, tien in ds:
            PHAI_THU.append(dict(sv=sv, ma_hk="20251", loai="khoan_thu", ma_lop=None, ma_kt=ma_kt, n_hp=None, he_so_lop=None,
                                 don_gia=None, so_tien=tien, han_nop=HAN["20251"], ma_mon=None, loai_dk=None))
    else:
        PHAI_THU.append(dict(sv=sv, ma_hk="20252", loai="khoan_thu", ma_lop=None, ma_kt="2526_BHYT12_DH", n_hp=None, he_so_lop=None,
                             don_gia=None, so_tien=631800, han_nop=HAN["20252"], ma_mon=None, loai_dk=None))
for sv in random.sample([s for s in SV if any(p["sv"] is s for p in PHAI_THU)], 4):
    hk = random.choice(["20251", "20252"])
    PHAI_THU.append(dict(sv=sv, ma_hk=hk, loai="phi_phat", ma_lop=None, ma_kt="PHI_XEM_LAI", n_hp=None, he_so_lop=None,
                         don_gia=None, so_tien=50000, han_nop=HK[hk][5] + timedelta(days=30), ma_mon=None, loai_dk=None))

for sv, ma_loai, ma_hk in HAUI_PENDING:
    HB.append(dict(sv=sv, ma_loai=ma_loai, ma_hk=ma_hk, nam_hoc=None, xep_loai=None, dt_ntb=None, nha_tai_tro=None,
                   so_tien=hoc_phi_lan_dau(sv, ma_hk), so_qd=f"{next(qd_so)}/QĐ-ĐHCN",
                   ngay_qd=HK[ma_hk][4] + timedelta(days=40)))

# ---------------------------------------------------------------------
# Đối tượng & chính sách
# ---------------------------------------------------------------------
SV_DT, SV_CS, NHAN_TIEN = [], [], []   # NHAN_TIEN: (sv, loai, so_tien, ngay, ghi_chu)
MUC_TRAN_2526 = {"DH_CNTT_KT": 1850000, "DH_KD_QL_PL": 1590000, "DH_NHAN_VAN_XH": 1690000}
for sv in SV:
    cfg, c = sv["cfg"], sv["c"]
    khoi = next(n[3] for n in NGANH if n[0] == c["nganh"])
    nhap = date(c["nam"], 9, 10)
    def chi_mghp(ty_le):
        for ngay in (date(2025, 12, 18), date(2026, 5, 20)):
            NHAN_TIEN.append((sv, "nhan_mghp", int(MUC_TRAN_2526[khoi] * ty_le * 5), ngay, "Chi miễn giảm học phí theo mức trần"))
    if cfg.get("khuyet_tat"):
        SV_DT.append((sv, "khuyet_tat", nhap, None, "da_duyet"))
        SV_CS.append((sv, "MIEN_KT", "khuyet_tat", nhap, None))
        chi_mghp(1.0)
    if cfg.get("ho_ngheo"):
        SV_DT += [(sv, "dtts", nhap, None, "da_duyet"),
                  (sv, "ho_ngheo", date(2025, 1, 1), date(2025, 12, 31), "da_duyet"),
                  (sv, "ho_ngheo", date(2026, 1, 1), date(2026, 12, 31), "da_duyet")]
        SV_CS += [(sv, "MIEN_DTTS_NGHEO", "ho_ngheo", nhap, None), (sv, "HT_CHI_PHI", "ho_ngheo", nhap, None)]
        chi_mghp(1.0)
        for ngay in (date(2025, 12, 18), date(2026, 5, 20)):
            NHAN_TIEN.append((sv, "nhan_ho_tro", int(LUONG_CO_SO * 0.6 * 5), ngay, "Hỗ trợ chi phí học tập 5 tháng"))
    if cfg.get("can_ngheo"):
        SV_DT += [(sv, "ho_can_ngheo", date(2024, 1, 1), date(2024, 12, 31), "da_duyet"),
                  (sv, "ho_can_ngheo", date(2025, 1, 1), date(2025, 12, 31), "da_duyet"),
                  (sv, "ho_can_ngheo", date(2026, 1, 1), date(2026, 12, 31), "cho_duyet")]
    if cfg.get("mo_coi"):
        SV_DT.append((sv, "mo_coi_1", nhap, None, "da_duyet"))
    if cfg.get("cha_tnld"):
        SV_DT.append((sv, "cha_me_tnld", nhap, None, "da_duyet"))
        SV_CS.append((sv, "GIAM50_TNLD", "cha_me_tnld", nhap, None))
        chi_mghp(0.5)
    if cfg.get("dan_toc", "Kinh") != "Kinh" and not cfg.get("ho_ngheo"):
        SV_DT.append((sv, "dtts", nhap, None, "da_duyet"))

# ---------------------------------------------------------------------
# Giao dịch: nạp tiền, thanh toán, nhận tiền (năm học 2025-2026)
# ---------------------------------------------------------------------
GD = []   # dict
for sv in SV:
    ds_pt = [p for p in PHAI_THU if p["sv"] is sv]
    if not ds_pt:
        continue
    kieu = random.choices(["dung_han", "tre", "thieu", "no"], [70, 14, 11, 5])[0]
    so_du = 0
    if random.random() < 0.35:
        du_cu = random.choice([50000, 120000, 250000, 480000])
        GD.append(dict(sv=sv, t=date(2025, 8, 20), loai="nap_tien", chieu="vao", tien=du_cu, pt=None, trang_thai="thanh_cong",
                       kenh="he_thong", ghi_chu="Số dư chuyển sang từ năm học trước"))
        so_du = du_cu
    vao = sorted([(n[3], n) for n in NHAN_TIEN if n[0] is sv], key=lambda t: t[0])
    vao += sorted([(h["ngay_qd"] + timedelta(days=21), ("hb", h)) for h in HB if h["sv"] is sv
                   and h["ngay_qd"] + timedelta(days=21) <= date(2026, 8, 31)
                   and (h["nam_hoc"] == "2025-2026" or (h["ma_hk"] and HK[h["ma_hk"]][0] == "2025-2026"))], key=lambda t: t[0])
    for ngay, n in vao:
        if n[0] == "hb":
            h = n[1]
            GD.append(dict(sv=sv, t=ngay, loai="nhan_hb", chieu="vao", tien=h["so_tien"], pt=None, hb=h, trang_thai="thanh_cong",
                           kenh="he_thong", ghi_chu="Nhận học bổng"))
        else:
            GD.append(dict(sv=sv, t=ngay, loai=n[1], chieu="vao", tien=n[2], pt=None, trang_thai="thanh_cong", kenh="he_thong", ghi_chu=n[4]))
    for ma_hk in ("20251", "20252", "20253"):
        ky = [p for p in ds_pt if p["ma_hk"] == ma_hk]
        if not ky:
            continue
        han = min(p["han_nop"] for p in ky)
        if kieu == "no" and ma_hk != "20251":
            continue
        tra = ky if kieu != "thieu" or ma_hk == "20251" else [p for p in ky if p["loai"] != "hoc_phi"] + [p for p in ky if p["loai"] == "hoc_phi"][:-2]
        can = sum(p["so_tien"] for p in tra)
        if not can:
            continue
        ngay = han - timedelta(days=random.randint(2, 20)) if kieu != "tre" else han + timedelta(days=random.randint(3, 25))
        nap = -(-(can - max(so_du, 0)) // 10000) * 10000
        if random.random() < 0.08:
            GD.append(dict(sv=sv, t=ngay - timedelta(days=1), loai="nap_tien", chieu="vao", tien=nap, pt=None,
                           trang_thai="that_bai", kenh="ngan_hang", ghi_chu="Giao dịch ngân hàng không thành công"))
        if nap > 0:
            GD.append(dict(sv=sv, t=ngay, loai="nap_tien", chieu="vao", tien=nap, pt=None, trang_thai="thanh_cong",
                           kenh=random.choice(["ngan_hang", "ngan_hang", "vi_dien_tu"]), ghi_chu=None))
            so_du += nap
        for p in tra:
            GD.append(dict(sv=sv, t=ngay, loai="thanh_toan", chieu="ra", tien=p["so_tien"], pt=p, trang_thai="thanh_cong",
                           kenh="he_thong", ghi_chu=None))
            so_du -= p["so_tien"]

# ---------------------------------------------------------------------
# Mật khẩu: argon2id, tham số mặc định của argon2-cffi (trùng pwdlib ở backend).
# Salt suy ra từ mã SV để file sinh ra lần nào cũng giống nhau. CHỈ dùng cho dữ liệu mẫu.
# ---------------------------------------------------------------------
_PH = PasswordHasher()


def hash_mat_khau(mat_khau: str) -> str:
    salt = hashlib.sha256(f"haui-sample-{SEED}-{mat_khau}".encode()).digest()[:16]
    return hash_secret(mat_khau.encode(), salt, time_cost=_PH.time_cost, memory_cost=_PH.memory_cost,
                       parallelism=_PH.parallelism, hash_len=_PH.hash_len, type=Type.ID).decode()


# ---------------------------------------------------------------------
# Bổ sung: giảng viên, lịch học, lịch thi, doanh nghiệp, thực tập.
# RNG riêng: thêm/bớt phần này không ảnh hưởng dữ liệu các bảng gốc.
# ---------------------------------------------------------------------
R2 = random.Random(SEED * 7 + 1)

KHOA_BO_SUNG = [
    ("LLCT", "Khoa Lý luận chính trị - Pháp luật"),
    ("KHCB", "Khoa Khoa học cơ bản"),
    ("GDTCQP", "Trung tâm Giáo dục thể chất và Quốc phòng"),
]
for ma, ten in KHOA_BO_SUNG:
    ins("khoa", ma_khoa=ma, ten=ten)

# Tiền tố mã môn → khoa phụ trách
KHOA_THEO_MON = {"IT": "CNTT", "ME": "COKHI", "AT": "COKHI", "EE": "DIEN", "BA": "KINHTE", "AC": "KINHTE",
                 "EN": "NGOAINGU", "FL": "NGOAINGU", "LP": "LLCT", "BS": "KHCB", "PE": "GDTCQP", "DC": "GDTCQP"}
SO_GV = {"CNTT": 8, "COKHI": 7, "DIEN": 7, "KINHTE": 7, "NGOAINGU": 8, "LLCT": 5, "KHCB": 6, "GDTCQP": 4}
HOC_VI = ["ths"] * 6 + ["ts"] * 3 + ["pgs"]

def ten_gv():
    # Như ten_nguoi() nhưng dùng R2: không được rút từ random toàn cục (xem đầu mục)
    while True:
        nu = R2.random() < 0.45
        ten = f"{R2.choice(HO)} {R2.choice(DEM_NU if nu else DEM_NAM)} {R2.choice(TEN_NU if nu else TEN_NAM)}"
        if ten not in DUNG_TEN:
            DUNG_TEN.add(ten)
            return ten


GV = {}   # ma_khoa -> [ma_gv]
stt_gv = 0
for ma_khoa, n in SO_GV.items():
    for _ in range(n):
        stt_gv += 1
        ma_gv = f"GV{stt_gv:04d}"
        ho_ten = ten_gv()
        ten_ks = ho_ten.lower().translate(KHONG_DAU).split()
        ins("giang_vien", ma_gv=ma_gv, ho_ten=ho_ten, ma_khoa=ma_khoa, hoc_vi=R2.choice(HOC_VI),
            email=f"{ten_ks[-1]}{''.join(w[0] for w in ten_ks[:-1])}@haui.edu.vn",
            sdt="09" + str(R2.randint(10000000, 99999999)))
        GV.setdefault(ma_khoa, []).append(ma_gv)

# Phòng theo loại học phần
TOA = ["A1", "A7", "A8", "A9", "A10"]
def phong_hoc(ma_mon):
    loai, th = M[ma_mon][6], M[ma_mon][5]
    if loai == "gdtc":
        return R2.choice(["Sân vận động", "Nhà thi đấu"])
    if loai == "gdqp":
        return "TT GDQP"
    if th == M[ma_mon][2]:   # học phần thuần thực hành
        return f"X{R2.randint(1, 6)}-{R2.randint(101, 305)}"
    return f"{R2.choice(TOA)}-{R2.randint(1, 8)}{R2.randint(1, 12):02d}"

# Gán giảng viên + phòng cho từng lớp học phần (sửa trực tiếp dòng lop_hp đã ghi)
for r in ROWS["lop_hp"]:
    khoa = KHOA_THEO_MON[r["ma_mon"][:2]]
    r["ma_gv"] = R2.choice(GV[khoa])
    r["phong"] = phong_hoc(r["ma_mon"])

# Lịch học: xếp ca theo (học kỳ, nhóm lớp) để các lớp cùng nhóm không trùng giờ.
# Ca sáng/chiều dùng cho lớp theo CTĐT, ca tối dùng cho lớp học lại/cải thiện chung.
CA_NGAY = [(t, 1) for t in range(2, 8)] + [(t, 7) for t in range(2, 8)] + [(t, 4) for t in range(2, 8)] + [(t, 10) for t in range(2, 8)]
CA_TOI = [(t, 13) for t in range(2, 9)]
NHOM_CUA_LOP = {ma_lop: nhom for (hk, mm, nhom), ma_lop in LOP.items()}
ca_da_dung = {}   # (ma_hk, nhom) -> set((thu, tiet))
LICH_HOC_ID = 0
for r in ROWS["lop_hp"]:
    ma_mon, ma_hk, loai = r["ma_mon"], r["ma_hk"], M[r["ma_mon"]][6]
    if loai in ("do_an", "thuc_tap"):
        continue   # không có lịch học cố định
    nhom = NHOM_CUA_LOP[r["ma_lop"]]
    phu = HK[ma_hk][1] == "phu"
    so_buoi = 3 if phu else (1 if M[ma_mon][2] <= 2 else 2)
    if loai == "gdqp":
        so_buoi = 5
    tuan_kt = 6 if phu else (4 if loai == "gdqp" else 15)
    kho = CA_TOI if nhom == "chung" else CA_NGAY
    dung = ca_da_dung.setdefault((ma_hk, nhom), set())
    trong = [c for c in kho if c not in dung] or list(kho)
    for thu, tiet in R2.sample(trong, min(so_buoi, len(trong))):
        dung.add((thu, tiet))
        LICH_HOC_ID += 1
        ins("lich_hoc", id=LICH_HOC_ID, ma_lop=r["ma_lop"], thu=thu, tiet_bd=tiet, so_tiet=3,
            phong=r["phong"], tuan_bd=1, tuan_kt=tuan_kt)

# Lịch thi: 1 ca thi / lớp học phần (trừ đồ án, thực tập), trong 3 tuần cuối học kỳ
HINH_THUC_THI = {"gdtc": "thuc_hanh", "gdqp": "trac_nghiem", "ngoai_ngu": "van_dap", "cntt": "thuc_hanh"}
THI_ID = 0
LICH_THI_CUA_LOP = {}
for r in ROWS["lop_hp"]:
    ma_mon, ma_hk, loai = r["ma_mon"], r["ma_hk"], M[r["ma_mon"]][6]
    if loai in ("do_an", "thuc_tap"):
        continue
    kt = HK[ma_hk][5]
    ngay = kt - timedelta(days=R2.randint(0, 20))
    if ngay.weekday() == 6:
        ngay -= timedelta(days=1)
    gio = R2.choice([7, 9, 13, 15])
    hinh_thuc = HINH_THUC_THI.get(loai) or (
        "thuc_hanh" if M[ma_mon][5] == M[ma_mon][2] else R2.choice(["tu_luan", "tu_luan", "trac_nghiem", "tieu_luan"]))
    THI_ID += 1
    LICH_THI_CUA_LOP[r["ma_lop"]] = THI_ID
    ins("lich_thi", id=THI_ID, ma_lop=r["ma_lop"], lan_thi=1,
        thoi_gian=datetime(ngay.year, ngay.month, ngay.day, gio, 0 if gio in (7, 13) else 30),
        so_phut={"van_dap": 30, "thuc_hanh": 90, "tieu_luan": 120}.get(hinh_thuc, 90),
        hinh_thuc=hinh_thuc, phong=r["phong"] if hinh_thuc == "thuc_hanh" else f"{R2.choice(TOA)}-{R2.randint(1, 8)}{R2.randint(1, 12):02d}")

# SV trong ca thi. Không đủ điều kiện dự thi ⇔ bản ghi điểm có điểm thi 0 (điểm liệt do không được thi):
# dùng đúng dữ liệu điểm đã sinh để hai bảng không mâu thuẫn nhau.
DIEM_CUA = {(sv["ma_sv"], d["ma_lop"]): d for sv in SV for d in sv["diem"]}
so_bd_lop = {}
for sv, ma_lop, ma_hk, loai_dk in DANG_KY:
    thi_id = LICH_THI_CUA_LOP.get(ma_lop)
    if not thi_id:
        continue
    d = DIEM_CUA.get((sv["ma_sv"], ma_lop))
    khong_du = d is not None and d["thi"] == 0.0
    so_bd_lop[thi_id] = so_bd_lop.get(thi_id, 0) + 1
    ins("lich_thi_sv", ma_lich_thi=thi_id, ma_sv=sv["ma_sv"], so_bd=so_bd_lop[thi_id],
        vi_tri=f"{(so_bd_lop[thi_id] - 1) // 6 + 1}-{(so_bd_lop[thi_id] - 1) % 6 + 1}",
        du_dieu_kien=not khong_du,
        ly_do="Không đủ điều kiện dự thi (điểm quá trình/chuyên cần)" if khong_du else None)

# Doanh nghiệp và thực tập: mỗi lần học học phần thực tập doanh nghiệp sinh 1 kỳ thực tập
DOANH_NGHIEP = [
    ("DN001", "Công ty Cổ phần Phần mềm Sao Bắc (minh họa)", "Quận Cầu Giấy, TP Hà Nội", "Phát triển phần mềm", "7480201"),
    ("DN002", "Công ty TNHH Giải pháp Dữ liệu Hồng Hà (minh họa)", "Quận Nam Từ Liêm, TP Hà Nội", "Dữ liệu và AI", "7480201"),
    ("DN003", "Công ty Cổ phần Viễn thông Thăng Long (minh họa)", "Quận Đống Đa, TP Hà Nội", "Hạ tầng mạng", "7480201"),
    ("DN004", "Công ty TNHH Ô tô Phương Đông (minh họa)", "Huyện Mê Linh, TP Hà Nội", "Lắp ráp ô tô", "7510205"),
    ("DN005", "Trung tâm Dịch vụ Ô tô Đại Việt (minh họa)", "Quận Long Biên, TP Hà Nội", "Bảo dưỡng, sửa chữa ô tô", "7510205"),
    ("DN006", "Công ty Cổ phần Điện lực Sông Đà (minh họa)", "Quận Hà Đông, TP Hà Nội", "Truyền tải và phân phối điện", "7510301"),
    ("DN007", "Công ty TNHH Tự động hóa Bắc Ninh (minh họa)", "TP Bắc Ninh, Tỉnh Bắc Ninh", "Tự động hóa công nghiệp", "7510301"),
    ("DN008", "Công ty TNHH Kiểm toán An Phát (minh họa)", "Quận Hoàn Kiếm, TP Hà Nội", "Kiểm toán, kế toán", "7340301"),
    ("DN009", "Công ty Cổ phần Thương mại Minh Long (minh họa)", "Quận Bắc Từ Liêm, TP Hà Nội", "Thương mại, phân phối", "7340301"),
    ("DN010", "Công ty Dịch thuật Toàn Cầu (minh họa)", "Quận Hai Bà Trưng, TP Hà Nội", "Biên phiên dịch", "7220201"),
    ("DN011", "Công ty Du lịch Hành Trình Xanh (minh họa)", "Quận Hoàn Kiếm, TP Hà Nội", "Du lịch lữ hành", "7220201"),
]
DN_THEO_NGANH = {}
for ma_dn, ten, dia_chi, linh_vuc, nganh in DOANH_NGHIEP:
    ins("doanh_nghiep", ma_dn=ma_dn, ten=ten, dia_chi=dia_chi, linh_vuc=linh_vuc,
        email=f"tuyendung@{ma_dn.lower()}.example.vn", sdt="024" + str(R2.randint(10000000, 99999999)))
    DN_THEO_NGANH.setdefault(nganh, []).append(ma_dn)

VI_TRI_TT = {"7480201": ["Thực tập sinh lập trình", "Thực tập sinh kiểm thử", "Thực tập sinh phân tích dữ liệu"],
             "7510205": ["Thực tập sinh kỹ thuật ô tô", "Thực tập sinh chẩn đoán"],
             "7510301": ["Thực tập sinh kỹ thuật điện", "Thực tập sinh vận hành"],
             "7340301": ["Thực tập sinh kế toán", "Thực tập sinh kiểm toán"],
             "7220201": ["Thực tập sinh biên dịch", "Thực tập sinh hướng dẫn viên"]}
TT_ID = 0
for sv in SV:
    nganh = sv["c"]["nganh"]
    khoa = next(n[2] for n in NGANH if n[0] == nganh)
    for d in sv["diem"]:
        if M[d["ma_mon"]][6] != "thuc_tap":
            continue
        bd = HK[d["ma_hk"]][4] + timedelta(days=7)
        TT_ID += 1
        ins("thuc_tap", id=TT_ID, ma_sv=sv["ma_sv"], ma_dn=R2.choice(DN_THEO_NGANH[nganh]), ma_hk=d["ma_hk"],
            ma_mon=d["ma_mon"], ma_gv=R2.choice(GV[khoa]), vi_tri=R2.choice(VI_TRI_TT[nganh]),
            tu_ngay=bd, den_ngay=bd + timedelta(weeks=10),
            trang_thai="hoan_thanh" if d["d10"] is not None else "dang_thuc_tap", diem=d["d10"])

# ---------------------------------------------------------------------
# Xuất SQL
# ---------------------------------------------------------------------
for sv in SV:
    ins("sinh_vien", ma_sv=sv["ma_sv"], ho_ten=sv["ho_ten"], ma_ctdt=sv["ctdt"], ma_ctdt_2=None, lop=sv["lop"],
        ngay_nhap_hoc=date(sv["c"]["nam"], 9, 10), trang_thai=sv["trang_thai"], hb_dau_vao=sv["cfg"].get("hb_dau_vao"),
        ngay_sinh=sv["ngay_sinh"], email=sv["email"], sdt=sv["sdt"], dia_chi=sv["dia_chi"], dan_toc=sv["dan_toc"], quoc_tich="Việt Nam")
for sv, ma_lop, ma_hk, loai_dk in DANG_KY:
    ins("dang_ky", ma_sv=sv["ma_sv"], ma_lop=ma_lop, ngay=HK[ma_hk][4] - timedelta(days=random.randint(10, 25)), loai=loai_dk, trang_thai="dang_ky")
for sv in SV:
    for d in sv["diem"]:
        ins("diem_hp", ma_sv=sv["ma_sv"], ma_mon=d["ma_mon"], ma_hk=d["ma_hk"], ma_lop=d["ma_lop"], lan_hoc=d["lan"],
            diem_qt=d["qt"], diem_thi=d["thi"], diem_10=d["d10"], diem_chu=d["chu"], chinh_thuc=d["chinh_thuc"])
    for ma_hk, k in sv["ket_qua"].items():
        ins("ket_qua_hk", ma_sv=sv["ma_sv"], ma_hk=ma_hk, tc_dk=k["tc_dk"], tc_dat=k["tc_dat"], tc_truot=k["tc_truot"],
            tb_hk=k["tb_hk"], tc_tich_luy=k["tc_tl"], tb_tich_luy=k["tb_tl"], xep_loai=k["xep_loai"], nam_thu=k["nam_thu"], canh_bao=k["canh_bao"])
    for ma_hk, d in sv["ren_luyen"].items():
        ins("ren_luyen", ma_sv=sv["ma_sv"], ma_hk=ma_hk, diem=d, xep_loai=xep_loai_rl(d))
    for loai, ok in sv["dk_tn"].items():
        ghi = {"ngoai_ngu": "Chứng chỉ VSTEP bậc 3 (B1)" if sv["c"]["nganh"] != "7220201" else "Chứng chỉ HSK 3",
               "cntt": "Hoàn thành học phần IT6000", "gdtc": "Hoàn thành GDTC 1–4", "gdqp": "Chứng chỉ GDQP-AN"}[loai]
        mon_dk = {"gdtc": [G["gdtc1"], G["gdtc2"], G["gdtc3"], G["gdtc4"]], "gdqp": [G["gdqp"]], "cntt": [G["cntt"]]}.get(loai)
        if ok and mon_dk:
            ngay = max(HK[d["ma_hk"]][5] for d in sv["diem"] if d["ma_mon"] in mon_dk and dat(d["chu"]))
        elif ok:
            ngay = date(2026, 4, 12) if sv["c"]["nam"] == 2023 else date(2025, random.choice([4, 6, 11]), random.randint(1, 28))
        ins("dk_tot_nghiep", ma_sv=sv["ma_sv"], loai=loai, dat=ok, ngay_dat=ngay if ok else None, ghi_chu=ghi if ok else None)
    # Bản gốc rút 53 ký tự random làm hash giả; giữ nguyên số lần rút để dữ liệu phía sau không bị lệch
    for _ in range(53):
        random.choice("./ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
    ins("tai_khoan", ten_dn=sv["ma_sv"], ma_sv=sv["ma_sv"], mat_khau=hash_mat_khau(sv["ma_sv"]))
    cfg = sv["cfg"]
    if cfg.get("ky_luat"):
        ht, ngay = cfg["ky_luat"]
        ins("ky_luat", ma_sv=sv["ma_sv"], hinh_thuc=ht, so_qd=f"{next(qd_so)}/QĐ-ĐHCN", ngay_qd=ngay,
            het_hieu_luc=ngay + timedelta(days=92 if ht == "khien_trach" else 183),
            noi_dung="Sử dụng tài liệu không được phép trong giờ thi" if ht == "khien_trach" else "Tái phạm vi phạm nội quy ký túc xá")
    if cfg.get("bao_luu"):
        ins("bien_dong", ma_sv=sv["ma_sv"], loai="bao_luu", so_qd=f"{next(qd_so)}/QĐ-ĐHCN", ngay_qd=date(2024, 1, 26),
            tu_ngay=date(2024, 2, 1), den_ngay=date(2025, 8, 31))
        ins("bien_dong", ma_sv=sv["ma_sv"], loai="tro_lai", so_qd=f"{next(qd_so)}/QĐ-ĐHCN", ngay_qd=date(2025, 8, 18),
            tu_ngay=date(2025, 9, 1), den_ngay=None)
    if sv.get("buoc_thoi_hoc"):
        ins("bien_dong", ma_sv=sv["ma_sv"], loai="buoc_thoi_hoc", so_qd=f"{next(qd_so)}/QĐ-ĐHCN", ngay_qd=sv["buoc_thoi_hoc"],
            tu_ngay=sv["buoc_thoi_hoc"], den_ngay=None)
    if sv["trang_thai"] == "tot_nghiep":
        ins("bien_dong", ma_sv=sv["ma_sv"], loai="tot_nghiep", so_qd=f"{next(qd_so)}/QĐ-ĐHCN", ngay_qd=date(2026, 7, 29),
            tu_ngay=date(2026, 7, 29), den_ngay=None)
    if cfg.get("thanh_tich"):
        loai, cap, giai, ten_ct, nam = cfg["thanh_tich"]
        ins("thanh_tich", ma_sv=sv["ma_sv"], nam_hoc=nam, loai=loai, cap=cap, giai=giai, cuoc_thi=ten_ct)

for sv, ma_dt, tu, den, tt in SV_DT:
    ins("sv_doi_tuong", ma_sv=sv["ma_sv"], ma_dt=ma_dt, tu_ngay=tu, den_ngay=den, trang_thai=tt)
for sv, ma_cs, ma_dt, tu, den in SV_CS:
    ins("sv_chinh_sach", ma_sv=sv["ma_sv"], ma_cs=ma_cs, ma_dt=ma_dt, tu_ngay=tu, den_ngay=den,
        so_qd=f"{next(qd_so)}/QĐ-ĐHCN", trang_thai="dang_huong")

for nh in ("2022-2023", "2023-2024", "2024-2025", "2025-2026"):
    for xl, tien in MUC_KKHT.items():
        ins("muc_hb", ma_loai="KKHT", nam_hoc=nh, xep_loai=xl, so_tien=tien, ty_le=None, ghi_chu="MINH HỌA — không phải mức thật")
ins("muc_hb", ma_loai="NTB", nam_hoc="2024-2025", xep_loai="chung", so_tien=MUC_NTB, ty_le=None,
    ghi_chu="MINH HỌA; đối tượng 2.1.2–2.1.4 nhận 120%, 2.1.1 nhận 150%")
ins("tham_so", ma="luong_co_so", gia_tri=LUONG_CO_SO, tu_ngay=date(2024, 7, 1), den_ngay=None, ghi_chu="NĐ 73/2024/NĐ-CP")

HB.sort(key=lambda h: (h["sv"]["ma_sv"], h["ma_hk"] or "", h["nam_hoc"] or ""))
for i, h in enumerate(HB, 1):
    h["id"] = i
    ins("hoc_bong", id=i, ma_sv=h["sv"]["ma_sv"], ma_loai=h["ma_loai"], ma_hk=h["ma_hk"], nam_hoc=h["nam_hoc"], xep_loai=h["xep_loai"],
        dt_ntb=h["dt_ntb"], nha_tai_tro=h["nha_tai_tro"], so_tien=h["so_tien"], so_qd=h["so_qd"], ngay_qd=h["ngay_qd"])
for i, p in enumerate(PHAI_THU, 1):
    p["id"] = i
    ins("phai_thu", id=i, ma_sv=p["sv"]["ma_sv"], ma_hk=p["ma_hk"], loai=p["loai"], ma_lop=p["ma_lop"], ma_kt=p["ma_kt"], n_hp=p["n_hp"],
        he_so_lop=p["he_so_lop"], don_gia=p["don_gia"], so_tien=p["so_tien"], han_nop=p["han_nop"], trang_thai="hieu_luc")
GD.sort(key=lambda g: (g["sv"]["ma_sv"], g["t"], g["chieu"] == "ra"))
for i, g in enumerate(GD, 1):
    gio = f"{random.randint(7, 22):02d}:{random.randint(0, 59):02d}:00"
    ins("giao_dich", id=i, ma_sv=g["sv"]["ma_sv"], thoi_gian=f"{g['t'].isoformat()} {gio}", loai=g["loai"], chieu=g["chieu"],
        so_tien=g["tien"], ma_phai_thu=g["pt"]["id"] if g["pt"] else None, ma_hb=g["hb"]["id"] if g.get("hb") else None,
        trang_thai=g["trang_thai"], kenh=g["kenh"], ghi_chu=g["ghi_chu"])

THU_TU = ["hoc_ky", "khoa", "nganh", "nien_khoa", "ctdt", "mon", "nhom_tu_chon", "ctdt_mon", "sinh_vien", "tai_khoan", "bien_dong",
          "ky_luat", "thanh_tich", "giang_vien", "lop_hp", "dang_ky", "diem_hp", "ket_qua_hk", "ren_luyen", "dk_tot_nghiep", "tham_so",
          "muc_hb", "hoc_bong", "sv_doi_tuong", "sv_chinh_sach", "phai_thu", "giao_dich",
          "lich_hoc", "lich_thi", "lich_thi_sv", "doanh_nghiep", "thuc_tap"]
with open(OUT, "w", encoding="utf-8") as f:
    f.write("-- Dữ liệu mẫu sinh bởi gen_sample_data.py (SEED = %d). Chốt 31/08/2026.\n" % SEED)
    f.write("-- Mức HB KKHT, NTB, tài trợ là MINH HỌA. Chạy sau 01 → 03.\nSET search_path = core;\n")
    for bang in THU_TU:
        rows = ROWS.get(bang, [])
        if not rows:
            continue
        ten = "private.tai_khoan" if bang == "tai_khoan" else bang
        cols = list(rows[0].keys())
        f.write(f"\n-- {bang}: {len(rows)} dòng\nINSERT INTO {ten} ({', '.join(cols)}) VALUES\n")
        f.write(",\n".join("(" + ", ".join(q(r[c]) for c in cols) + ")" for r in rows) + ";\n")
    f.write("\nSELECT setval(pg_get_serial_sequence('core.hoc_bong', 'id'), (SELECT max(id) FROM core.hoc_bong));\n")
    f.write("SELECT setval(pg_get_serial_sequence('core.phai_thu', 'id'), (SELECT max(id) FROM core.phai_thu));\n")
    f.write("SELECT setval(pg_get_serial_sequence('core.giao_dich', 'id'), (SELECT max(id) FROM core.giao_dich));\n")
    for bang in ("lich_hoc", "lich_thi", "thuc_tap"):
        f.write(f"SELECT setval(pg_get_serial_sequence('core.{bang}', 'id'), (SELECT max(id) FROM core.{bang}));\n")

print({b: len(ROWS.get(b, [])) for b in THU_TU})
