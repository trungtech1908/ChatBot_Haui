from itertools import groupby

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from chatbot_haui.db.models import (
    CT_CTDT, CT_DT, CT_NMH, KetQuaMonHoc, LichThiSV, LopHoc, NhomMH, SinhVien, SinhVienLopHoc, TaiKhoan,
    ThucTap,
)
from chatbot_haui.schema.student import (
    AcademicSummary, Curriculum, CurriculumCourse, CurriculumGroup, ExamItem, Finance, Grade, Graduation, Internship,
    Policy, Profile, ScheduleItem, SemesterSummary, Transaction,
)

# Thứ tự hiển thị nhóm môn: chính trị, KHCB, ngoại ngữ, thể chất, cơ sở ngành, chuyên ngành, tự chọn, thực tập
GROUP_ORDER = ["G_CTPL", "KHCB", "G_NN", "G_GDTC", "_CS", "_CN", "_TC", "_TTKL"]


def _group_rank(code: str) -> int:
    return next((i for i, key in enumerate(GROUP_ORDER) if key in code), len(GROUP_ORDER))


def _num(value) -> float | None:
    return float(value) if value is not None else None


def _student(db: Session, account: TaiKhoan, *options) -> SinhVien:
    return db.scalars(select(SinhVien).where(SinhVien.maSV == account.maSV).options(*options)).one()


def get_profile(db: Session, account: TaiKhoan) -> Profile:
    sv = _student(db, account, joinedload(SinhVien.doiTuong), joinedload(SinhVien.ct_dt).joinedload(CT_DT.khoa_rel))
    dt, ct = sv.doiTuong, sv.ct_dt
    return Profile(
        student_id=sv.maSV,
        username=account.tenTaiKhoan,
        full_name=sv.hoTen,
        email=sv.email,
        date_of_birth=sv.NgaySinh,
        phone=sv.soDT,
        address=sv.diaChi,
        major=ct.nganhHoc if ct else None,
        cohort=ct.khoaHoc if ct else None,
        faculty=ct.khoa_rel.tenKhoa if ct and ct.khoa_rel else None,
        policy=Policy(
            ethnicity=dt.dan_Toc, nationality=dt.quoc_Tich, poor_household=bool(dt.ho_Ngheo),
            near_poor_household=bool(dt.ho_Can_Ngheo), orphan=bool(dt.mo_Coi), disabled=bool(dt.khuyet_Tan),
        ) if dt else None,
    )


def get_curriculum(db: Session, account: TaiKhoan) -> Curriculum | None:
    sv = _student(db, account, joinedload(SinhVien.ct_dt).selectinload(CT_DT.ct_ctdt).joinedload(CT_CTDT.nhomMH)
                  .selectinload(NhomMH.ct_nmh).joinedload(CT_NMH.monHoc_rel))
    ct = sv.ct_dt
    if not ct:
        return None
    groups = sorted((link.nhomMH for link in ct.ct_ctdt if link.nhomMH), key=lambda g: _group_rank(g.maNhom))
    return Curriculum(
        major=ct.nganhHoc,
        cohort=ct.khoaHoc,
        required_credits=ct.soTC_YeuCau,
        groups=[
            CurriculumGroup(
                code=g.maNhom, name=g.TenNhom, type=g.loaiNhom, required_credits=g.soTC_YC,
                courses=[
                    CurriculumCourse(code=c.maMH, name=c.monHoc_rel.tenMonHoc, credits=c.monHoc_rel.soTC, semester=c.ky)
                    for c in sorted(g.ct_nmh, key=lambda c: c.ky or 0)
                ],
            )
            for g in groups
        ],
    )


def get_schedule(db: Session, account: TaiKhoan) -> list[ScheduleItem]:
    sv = _student(db, account, selectinload(SinhVien.lopHocDangKy).joinedload(SinhVienLopHoc.lopHoc_rel).options(
        selectinload(LopHoc.lichHoc), joinedload(LopHoc.monHoc_rel), joinedload(LopHoc.giangVien_rel)))
    return [
        ScheduleItem(
            course_name=lop.monHoc_rel.tenMonHoc if lop.monHoc_rel else None,
            class_code=lop.maLH,
            weekday=lich.thu,
            periods=lich.tietHoc,
            room=lop.soPhong,
            lecturer=lop.giangVien_rel.hoTen if lop.giangVien_rel else None,
        )
        for lop in (dk.lopHoc_rel for dk in sv.lopHocDangKy)
        for lich in lop.lichHoc
    ]


def get_exams(db: Session, account: TaiKhoan) -> list[ExamItem]:
    sv = _student(db, account, selectinload(SinhVien.lichThiSV).joinedload(LichThiSV.lichThi_rel))
    return [
        ExamItem(
            candidate_number=t.soBD,
            exam_code=t.maLT,
            start_time=t.lichThi_rel.gioBD if t.lichThi_rel else None,
            room=t.lichThi_rel.soPhong if t.lichThi_rel else None,
            seat=t.viTri,
            format=t.lichThi_rel.hinhThucThi if t.lichThi_rel else None,
            eligible=bool(t.dieuKienThi),
        )
        for t in sv.lichThiSV
    ]


def get_internships(db: Session, account: TaiKhoan) -> list[Internship]:
    sv = _student(db, account, selectinload(SinhVien.thucTapRecords).options(
        joinedload(ThucTap.doanhNghiep_rel), joinedload(ThucTap.giangVien_rel)))
    return [
        Internship(
            company=t.doanhNghiep_rel.tenDN if t.doanhNghiep_rel else None,
            position=t.viTriTT,
            address=t.doanhNghiep_rel.diaChi if t.doanhNghiep_rel else None,
            supervisor=t.giangVien_rel.hoTen if t.giangVien_rel else None,
            company_email=t.doanhNghiep_rel.email if t.doanhNghiep_rel else None,
        )
        for t in sv.thucTapRecords
    ]


def get_grades(db: Session, account: TaiKhoan) -> list[Grade]:
    sv = _student(db, account, selectinload(SinhVien.ketQuaMonHoc).joinedload(KetQuaMonHoc.monHoc_rel))
    return [
        Grade(
            course_code=kq.maMH,
            course_name=kq.monHoc_rel.tenMonHoc if kq.monHoc_rel else None,
            tx1=_num(kq.tx1), tx2=_num(kq.tx2), midterm=_num(kq.giuaKy), final=_num(kq.BaiThi),
            total=_num(kq.diemGPA), letter=kq.diemChu,
        )
        for kq in sv.ketQuaMonHoc
    ]


def get_academic_summary(db: Session, account: TaiKhoan) -> AcademicSummary:
    sv = _student(db, account, selectinload(SinhVien.ketQuaMonHoc).joinedload(KetQuaMonHoc.ketQuaHocKy_rel),
                  joinedload(SinhVien.dieuKienTotNghiep))
    results = sorted((kq for kq in sv.ketQuaMonHoc if kq.ketQuaHocKy_rel), key=lambda kq: kq.ketQuaHocKy_rel.hocKy or 0)
    semesters = []
    for _, items in groupby(results, key=lambda kq: kq.ketQuaHocKy_rel.hocKy):
        items = list(items)
        hk = items[0].ketQuaHocKy_rel
        semesters.append(SemesterSummary(semester=hk.hocKy, gpa=_num(hk.diemTBC), credits=hk.TongTC, course_count=len(items)))

    dk = sv.dieuKienTotNghiep
    graduation = Graduation(
        gpa=_num(dk.tb_GPA), credits_ok=bool(dk.DKSoTC), physical_education_ok=bool(dk.DKTheChat),
        language_ok=bool(dk.DKNgoaiNgu), defense_education_ok=bool(dk.DK_GDQP),
    ) if dk else None
    return AcademicSummary(semesters=semesters, graduation=graduation)


def get_finance(db: Session, account: TaiKhoan) -> Finance:
    sv = _student(db, account, joinedload(SinhVien.taiChinh), selectinload(SinhVien.giaoDich))
    tc = sv.taiChinh
    return Finance(
        balance=int(tc.soDu or 0) if tc else 0,
        debt=int(tc.no or 0) if tc else 0,
        scholarship=int(tc.hocBong or 0) if tc else 0,
        transactions=[
            Transaction(code=gd.maGD, name=gd.tenGD, note=gd.GhiChu,
                        amount=int(gd.ThanhTien) if gd.ThanhTien is not None else None, is_income=bool(gd.Cong_Tru))
            for gd in sv.giaoDich
        ],
    )
