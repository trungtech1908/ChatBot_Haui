"""Dữ liệu cho các trang /students/me/*.

Số liệu tổng hợp (công nợ, số dư, tiến độ CTĐT, kết quả học kỳ) đọc từ view chatbot.* — cùng
công thức mà Text2SQL dùng, không tính lại lần thứ hai ở Python. Muốn đọc view phải gắn
app.ma_sv vào transaction hiện tại (set_config(..., true) → hết hiệu lực khi transaction kết thúc).
Thông tin cá nhân (SĐT, địa chỉ, ngày sinh) không có trong view nên đọc thẳng core.sinh_vien.
"""
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from chatbot_haui.db.models import SinhVien, TaiKhoan
from chatbot_haui.schema.student import (
    AcademicSummary, Curriculum, CurriculumCourse, CurriculumGroup, ExamItem, Finance, Grade, Graduation, Internship,
    Policy, Profile, ScheduleItem, SemesterSummary, Transaction,
)

EXAM_FORMAT = {
    "tu_luan": "Tự luận", "trac_nghiem": "Trắc nghiệm", "van_dap": "Vấn đáp",
    "thuc_hanh": "Thực hành", "tieu_luan": "Tiểu luận",
}
INTERNSHIP_STATUS = {"dang_thuc_tap": "Đang thực tập", "hoan_thanh": "Hoàn thành", "huy": "Đã hủy"}
TRANSACTION_NAME = {
    "nap_tien": "Nạp tiền", "rut_tien": "Rút tiền", "thanh_toan": "Thanh toán", "hoan_tien": "Hoàn tiền",
    "nhan_hb": "Nhận học bổng", "nhan_mghp": "Nhận miễn giảm học phí", "nhan_ho_tro": "Nhận hỗ trợ",
}
TRANSACTION_STATUS = {"thanh_cong": "Thành công", "that_bai": "Thất bại", "dang_xu_ly": "Đang xử lý"}
PAYMENT_KIND = {"hoc_phi": "Học phí", "khoan_thu": "Khoản thu", "phi_phat": "Phí", "khac": "Khoản khác"}


def _num(value) -> float | None:
    return float(value) if isinstance(value, Decimal) else value


def _rows(db: Session, sql: str, **params) -> list[dict]:
    return [dict(r._mapping) for r in db.execute(text(sql), params)]


def _scope(db: Session, account: TaiKhoan) -> None:
    """Gắn phạm vi dữ liệu cho view chatbot.v_* trong transaction hiện tại của session."""
    db.execute(text("SELECT set_config('app.ma_sv', :ma_sv, true)"), {"ma_sv": account.ma_sv})


def get_profile(db: Session, account: TaiKhoan) -> Profile:
    sv = db.get(SinhVien, account.ma_sv)
    info = _rows(db, """
        SELECT n.ten AS nganh, k.ten AS khoa,
               CASE nk.bac WHEN 'dai_hoc' THEN 'Cử nhân K' WHEN 'ky_su' THEN 'Kỹ sư K' ELSE 'Cao đẳng K' END
                 || nk.so_khoa AS ten_khoa
        FROM core.ctdt c
        JOIN core.nganh n ON n.ma_nganh = c.ma_nganh
        JOIN core.khoa k ON k.ma_khoa = n.ma_khoa
        JOIN core.nien_khoa nk ON nk.ma_nk = c.ma_nk
        WHERE c.ma_ctdt = :ma_ctdt""", ma_ctdt=sv.ma_ctdt)[0]
    # Đối tượng đang được công nhận (đã duyệt, còn hiệu lực)
    active = {r["ma_dt"] for r in _rows(db, """
        SELECT ma_dt FROM core.sv_doi_tuong
        WHERE ma_sv = :ma_sv AND trang_thai = 'da_duyet' AND tu_ngay <= CURRENT_DATE
          AND (den_ngay IS NULL OR den_ngay >= CURRENT_DATE)""", ma_sv=sv.ma_sv)}
    return Profile(
        student_id=sv.ma_sv,
        username=account.ten_dn,
        full_name=sv.ho_ten,
        email=sv.email,
        date_of_birth=sv.ngay_sinh,
        phone=sv.sdt,
        address=sv.dia_chi,
        major=info["nganh"],
        cohort=info["ten_khoa"],
        faculty=info["khoa"],
        policy=Policy(
            ethnicity=sv.dan_toc,
            nationality=sv.quoc_tich,
            poor_household="ho_ngheo" in active,
            near_poor_household="ho_can_ngheo" in active,
            orphan=bool(active & {"mo_coi_1", "khong_noi_nuong_tua"}),
            disabled="khuyet_tat" in active,
        ),
    )


def get_curriculum(db: Session, account: TaiKhoan) -> Curriculum | None:
    _scope(db, account)
    profile = _rows(db, "SELECT nganh, ten_khoa, tc_yeu_cau, ma_ctdt FROM chatbot.v_sinh_vien")
    if not profile:
        return None
    p = profile[0]
    courses = _rows(db, """
        SELECT cm.ma_mon, m.ten, m.so_tc, cm.bat_buoc, cm.hk_thu, nt.ma_nhom, nt.ten AS ten_nhom, nt.so_tc AS tc_nhom
        FROM core.ctdt_mon cm
        JOIN core.mon m ON m.ma_mon = cm.ma_mon
        LEFT JOIN core.nhom_tu_chon nt ON nt.ma_nhom = cm.ma_nhom
        WHERE cm.ma_ctdt = :ma_ctdt
        ORDER BY cm.hk_thu, cm.ma_mon""", ma_ctdt=p["ma_ctdt"])

    required = [c for c in courses if c["bat_buoc"]]
    groups = [CurriculumGroup(
        code="BAT_BUOC", name="Học phần bắt buộc", type="Bắt buộc",
        required_credits=sum(c["so_tc"] for c in required),
        courses=[CurriculumCourse(code=c["ma_mon"], name=c["ten"], credits=c["so_tc"], semester=c["hk_thu"])
                 for c in required],
    )]
    electives = defaultdict(list)
    for c in courses:
        if not c["bat_buoc"]:
            electives[(c["ma_nhom"], c["ten_nhom"], c["tc_nhom"])].append(c)
    for (code, name, credits), items in electives.items():
        groups.append(CurriculumGroup(
            code=code, name=name, type="Tự chọn", required_credits=credits,
            courses=[CurriculumCourse(code=c["ma_mon"], name=c["ten"], credits=c["so_tc"], semester=c["hk_thu"])
                     for c in items],
        ))
    return Curriculum(major=p["nganh"], cohort=p["ten_khoa"], required_credits=p["tc_yeu_cau"], groups=groups)


def get_schedule(db: Session, account: TaiKhoan) -> list[ScheduleItem]:
    """Thời khóa biểu của học kỳ gần nhất mà sinh viên có lớp."""
    _scope(db, account)
    rows = _rows(db, """
        SELECT * FROM chatbot.v_lich_hoc
        WHERE ma_hk = (SELECT max(ma_hk) FROM chatbot.v_lich_hoc)
        ORDER BY thu, tiet_bd""")
    return [
        ScheduleItem(
            semester=r["hoc_ky"], course_name=r["mon"], class_code=r["ma_lop"], weekday=r["thu"],
            periods=f"Tiết {r['tiet_bd']}–{r['tiet_kt']}",
            weeks=f"Tuần {r['tuan_bd']}–{r['tuan_kt']}" if r["tuan_bd"] else None,
            room=r["phong"], lecturer=r["giang_vien"],
        )
        for r in rows
    ]


def get_exams(db: Session, account: TaiKhoan) -> list[ExamItem]:
    """Lịch thi của học kỳ gần nhất có lịch thi."""
    _scope(db, account)
    rows = _rows(db, """
        SELECT * FROM chatbot.v_lich_thi
        WHERE ma_hk = (SELECT max(ma_hk) FROM chatbot.v_lich_thi)
        ORDER BY thoi_gian""")
    return [
        ExamItem(
            semester=r["hoc_ky"], course_name=r["mon"], candidate_number=r["so_bd"], exam_code=r["ma_lop"],
            start_time=r["thoi_gian"], duration_minutes=r["so_phut"], room=r["phong"], seat=r["vi_tri"],
            format=EXAM_FORMAT.get(r["hinh_thuc"], r["hinh_thuc"]), eligible=r["du_dieu_kien"],
            ineligible_reason=r["ly_do"],
        )
        for r in rows
    ]


def get_internships(db: Session, account: TaiKhoan) -> list[Internship]:
    _scope(db, account)
    # Email doanh nghiệp không có trong view chatbot (view chỉ phục vụ hỏi đáp), lấy từ core
    emails = {r["ten"]: r["email"] for r in _rows(db, """
        SELECT dn.ten, dn.email FROM core.thuc_tap t JOIN core.doanh_nghiep dn ON dn.ma_dn = t.ma_dn
        WHERE t.ma_sv = :ma_sv""", ma_sv=account.ma_sv)}
    return [
        Internship(
            semester=r["hoc_ky"], company=r["doanh_nghiep"], position=r["vi_tri"], address=r["dia_chi"],
            field=r["linh_vuc"], supervisor=r["gv_huong_dan"], company_email=emails.get(r["doanh_nghiep"]),
            start_date=r["tu_ngay"], end_date=r["den_ngay"],
            status=INTERNSHIP_STATUS.get(r["trang_thai"], r["trang_thai"]), score=_num(r["diem"]),
        )
        for r in _rows(db, "SELECT * FROM chatbot.v_thuc_tap ORDER BY tu_ngay DESC")
    ]


def get_grades(db: Session, account: TaiKhoan) -> list[Grade]:
    _scope(db, account)
    return [
        Grade(
            semester=r["hoc_ky"], semester_code=r["ma_hk"], course_code=r["ma_mon"], course_name=r["mon"],
            credits=r["so_tc"], attempt=r["lan_hoc"], process=_num(r["diem_qt"]), exam=_num(r["diem_thi"]),
            total=_num(r["diem_10"]), letter=r["diem_chu"], official=r["chinh_thuc"],
        )
        for r in _rows(db, "SELECT * FROM chatbot.v_diem ORDER BY ma_hk DESC, ma_mon")
    ]


def get_academic_summary(db: Session, account: TaiKhoan) -> AcademicSummary:
    _scope(db, account)
    # Số học phần mỗi HK chính (gộp HK phụ, đúng cách ket_qua_hk tính)
    course_count = {r["ma_hk_chinh"]: r["n"] for r in _rows(
        db, "SELECT ma_hk_chinh, count(*) AS n FROM chatbot.v_diem GROUP BY ma_hk_chinh")}
    results = _rows(db, "SELECT * FROM chatbot.v_ket_qua_hk ORDER BY ma_hk")
    semesters = [
        SemesterSummary(
            code=r["ma_hk"], semester=r["hoc_ky"], gpa=_num(r["tb_hk"]), cumulative_gpa=_num(r["tb_tich_luy"]),
            credits=r["tc_dat"], course_count=course_count.get(r["ma_hk"], 0), conduct_score=r["diem_rl"],
            warning=r["canh_bao"],
        )
        for r in results
    ]

    conditions = {r["loai"]: r["dat"] for r in _rows(db, "SELECT loai, dat FROM chatbot.v_tot_nghiep")}
    required = _rows(db, "SELECT tc_yeu_cau FROM chatbot.v_sinh_vien")
    graduation = None
    if results or conditions:
        last = results[-1] if results else {}
        credits = last.get("tc_tich_luy") or 0
        graduation = Graduation(
            gpa=_num(last.get("tb_tich_luy")),
            credits=credits,
            credits_ok=bool(required) and credits >= required[0]["tc_yeu_cau"],
            physical_education_ok=conditions.get("gdtc", False),
            language_ok=conditions.get("ngoai_ngu", False),
            defense_education_ok=conditions.get("gdqp", False),
        )
    return AcademicSummary(semesters=semesters, graduation=graduation)


def get_finance(db: Session, account: TaiKhoan) -> Finance:
    _scope(db, account)
    balance = db.execute(text("SELECT so_du FROM chatbot.v_so_du")).scalar() or 0
    debt = db.execute(text("SELECT COALESCE(SUM(con_no), 0) FROM chatbot.v_cong_no WHERE con_no > 0")).scalar()
    scholarship = db.execute(text("SELECT COALESCE(SUM(so_tien), 0) FROM chatbot.v_hoc_bong")).scalar()
    # Nội dung khoản thanh toán (tên môn / khoản thu) lấy qua phai_thu
    rows = _rows(db, """
        SELECT g.id, g.thoi_gian, g.loai, g.chieu, g.so_tien, g.trang_thai, g.ghi_chu,
               p.loai AS loai_pt, COALESCE(m.ten, kt.ten) AS noi_dung, hk.ten AS hoc_ky
        FROM core.giao_dich g
        LEFT JOIN core.phai_thu p  ON p.id = g.ma_phai_thu
        LEFT JOIN core.lop_hp l    ON l.ma_lop = p.ma_lop
        LEFT JOIN core.mon m       ON m.ma_mon = l.ma_mon
        LEFT JOIN core.khoan_thu kt ON kt.ma_kt = p.ma_kt
        LEFT JOIN core.hoc_ky hk   ON hk.ma_hk = p.ma_hk
        WHERE g.ma_sv = :ma_sv
        ORDER BY g.thoi_gian DESC, g.id DESC""", ma_sv=account.ma_sv)

    def name(r) -> str:
        base = TRANSACTION_NAME.get(r["loai"], r["loai"])
        if r["loai"] == "thanh_toan" and r["noi_dung"]:
            return f"{base} {PAYMENT_KIND.get(r['loai_pt'], '').lower()}: {r['noi_dung']}".replace("  ", " ")
        return base

    return Finance(
        balance=int(balance),
        debt=int(debt),
        scholarship=int(scholarship),
        transactions=[
            Transaction(
                code=f"GD{r['id']:06d}", time=r["thoi_gian"], name=name(r),
                note=r["ghi_chu"] or r["hoc_ky"],
                amount=int(r["so_tien"]), is_income=r["chieu"] == "vao",
                status=TRANSACTION_STATUS.get(r["trang_thai"], r["trang_thai"]),
            )
            for r in rows
        ],
    )
