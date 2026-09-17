from fastapi import APIRouter, HTTPException

from chatbot_haui.api.deps import CurrentAccount, DbSession
from chatbot_haui.schema.student import (
    AcademicSummary, Curriculum, ExamItem, Finance, Grade, Internship, Profile, ScheduleItem,
)
from chatbot_haui.services import student as student_service

router = APIRouter(prefix="/students/me", tags=["students"])


@router.get("")
def profile(db: DbSession, account: CurrentAccount) -> Profile:
    return student_service.get_profile(db, account)


@router.get("/curriculum")
def curriculum(db: DbSession, account: CurrentAccount) -> Curriculum:
    result = student_service.get_curriculum(db, account)
    if not result:
        raise HTTPException(404, "Sinh viên chưa có chương trình đào tạo")
    return result


@router.get("/schedule")
def schedule(db: DbSession, account: CurrentAccount) -> list[ScheduleItem]:
    return student_service.get_schedule(db, account)


@router.get("/exams")
def exams(db: DbSession, account: CurrentAccount) -> list[ExamItem]:
    return student_service.get_exams(db, account)


@router.get("/internships")
def internships(db: DbSession, account: CurrentAccount) -> list[Internship]:
    return student_service.get_internships(db, account)


@router.get("/grades")
def grades(db: DbSession, account: CurrentAccount) -> list[Grade]:
    return student_service.get_grades(db, account)


@router.get("/academic-summary")
def academic_summary(db: DbSession, account: CurrentAccount) -> AcademicSummary:
    return student_service.get_academic_summary(db, account)


@router.get("/finance")
def finance(db: DbSession, account: CurrentAccount) -> Finance:
    return student_service.get_finance(db, account)
