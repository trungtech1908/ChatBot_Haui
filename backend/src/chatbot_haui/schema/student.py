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
    semester: int | None


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
    course_name: str | None
    class_code: str
    weekday: int | None
    periods: str | None  # 'Tiết 1–3'
    weeks: str | None  # 'Tuần 1–15'
    room: str | None
    lecturer: str | None


class ExamItem(ApiModel):
    semester: str
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
    official: bool  # lần học dùng tính điểm tích lũy


class SemesterSummary(ApiModel):
    code: str
    semester: str
    gpa: float | None  # TB học kỳ, hệ 4
    cumulative_gpa: float | None
    credits: int | None  # TC đạt trong kỳ
    course_count: int
    conduct_score: int | None  # điểm rèn luyện
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
    time: datetime
    name: str | None
    note: str | None
    amount: int | None
    is_income: bool
    status: str


class Finance(ApiModel):
    balance: int
    debt: int
    scholarship: int  # tổng học bổng đã nhận
    transactions: list[Transaction]
