from datetime import date, datetime

from chatbot_haui.schema.base import ApiModel


class Policy(ApiModel):
    ethnicity: str | None
    nationality: str | None
    poor_household: bool
    near_poor_household: bool
    orphan: bool
    disabled: bool


class Profile(ApiModel):
    student_id: str
    username: str
    full_name: str | None
    email: str | None
    date_of_birth: date | None
    phone: str | None
    address: str | None
    major: str | None
    cohort: str | None
    faculty: str | None
    policy: Policy | None


class CurriculumCourse(ApiModel):
    code: str
    name: str
    credits: int
    semester: int | None  # học kỳ thứ mấy theo kế hoạch chuẩn
    status: str  # da_dat | chua_dat | chua_co_diem | chua_hoc
    letter: str | None  # điểm chữ của lần học chính thức
    taken_semester: str | None  # mã học kỳ đã học


class CurriculumGroup(ApiModel):
    code: str
    name: str | None
    type: str | None
    required_credits: int | None
    courses: list[CurriculumCourse]


class Curriculum(ApiModel):
    major: str
    cohort: str
    required_credits: int | None
    groups: list[CurriculumGroup]


class ScheduleItem(ApiModel):
    semester: str
    semester_code: str
    start_period: int
    end_period: int
    course_name: str | None
    class_code: str
    weekday: int | None
    periods: str | None  # 'Tiết 1–3'
    weeks: str | None  # 'Tuần 1–15'
    room: str | None
    lecturer: str | None


class ExamItem(ApiModel):
    semester: str
    semester_code: str
    course_name: str | None
    candidate_number: int
    exam_code: str | None  # mã lớp học phần
    start_time: datetime | None
    duration_minutes: int | None
    room: str | None
    seat: str | None
    format: str | None
    eligible: bool
    ineligible_reason: str | None


class Internship(ApiModel):
    semester: str
    company: str | None
    position: str | None
    address: str | None
    field: str | None
    supervisor: str | None
    company_email: str | None
    start_date: date | None
    end_date: date | None
    status: str
    score: float | None


class Grade(ApiModel):
    semester: str
    semester_code: str
    course_code: str | None
    course_name: str | None
    credits: int
    attempt: int  # lần học: 1 = lần đầu
    process: float | None  # điểm quá trình
    exam: float | None  # điểm thi
    total: float | None  # điểm học phần hệ 10
    letter: str | None
    grade4: float | None  # điểm hệ 4
    passed: bool | None  # None: chưa có kết quả (I, X)
    counts_gpa: bool  # có tính vào điểm trung bình không (GDTC, GDQP thì không)
    registration: str | None  # lan_dau | hoc_lai | cai_thien | hoc_doi
    course_type: str  # thuong | gdtc | gdqp | cntt | ngoai_ngu | thuc_tap | do_an
    official: bool  # lần học dùng tính điểm tích lũy


class SemesterSummary(ApiModel):
    code: str
    semester: str
    gpa: float | None  # TB học kỳ, hệ 4
    cumulative_gpa: float | None
    credits: int | None  # TC đạt trong kỳ
    credits_registered: int | None
    credits_failed: int | None
    cumulative_credits: int | None
    classification: str | None  # xếp loại học lực kỳ: xuat_sac | gioi | kha | trung_binh | yeu | kem
    course_count: int
    conduct_score: int | None  # điểm rèn luyện
    conduct_classification: str | None
    warning: bool  # cảnh báo học tập


class Graduation(ApiModel):
    gpa: float | None  # TB tích lũy, hệ 4
    credits: int  # TC tích lũy
    credits_ok: bool
    physical_education_ok: bool
    language_ok: bool
    defense_education_ok: bool


class AcademicSummary(ApiModel):
    semesters: list[SemesterSummary]
    graduation: Graduation | None


class Transaction(ApiModel):
    code: str
    kind: str  # nap_tien | thanh_toan | nhan_hb | nhan_mghp | nhan_ho_tro | rut_tien | hoan_tien
    time: datetime
    name: str | None
    note: str | None
    amount: int | None
    is_income: bool
    status: str


class SemesterDebt(ApiModel):
    semester_code: str
    semester: str
    total: int  # phải thu
    paid: int
    remaining: int
    due_date: date | None  # hạn sớm nhất của khoản còn nợ


class Payable(ApiModel):
    id: int
    semester_code: str
    semester: str
    kind: str  # hoc_phi | khoan_thu | phi_phat | khac
    content: str | None  # tên môn hoặc tên khoản thu
    amount: int
    paid: int
    remaining: int
    due_date: date | None


class Finance(ApiModel):
    balance: int
    debt: int
    scholarship: int  # tổng học bổng đã nhận
    debts: list[SemesterDebt]
    payables: list[Payable]
    transactions: list[Transaction]
