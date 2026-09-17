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
    course_name: str | None
    class_code: str
    weekday: int | None
    periods: str | None
    room: int | None
    lecturer: str | None


class ExamItem(ApiModel):
    candidate_number: int
    exam_code: str | None
    start_time: datetime | None
    room: int | None
    seat: str | None
    format: str | None
    eligible: bool


class Internship(ApiModel):
    company: str | None
    position: str | None
    address: str | None
    supervisor: str | None
    company_email: str | None


class Grade(ApiModel):
    course_code: str | None
    course_name: str | None
    tx1: float | None
    tx2: float | None
    midterm: float | None
    final: float | None
    total: float | None
    letter: str | None


class SemesterSummary(ApiModel):
    semester: int | None
    gpa: float | None
    credits: int | None
    course_count: int


class Graduation(ApiModel):
    gpa: float | None
    credits_ok: bool
    physical_education_ok: bool
    language_ok: bool
    defense_education_ok: bool


class AcademicSummary(ApiModel):
    semesters: list[SemesterSummary]
    graduation: Graduation | None


class Transaction(ApiModel):
    code: str
    name: str | None
    note: str | None
    amount: int | None
    is_income: bool


class Finance(ApiModel):
    balance: int
    debt: int
    scholarship: int
    transactions: list[Transaction]
