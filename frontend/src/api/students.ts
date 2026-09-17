import { useQuery } from '@tanstack/react-query'

import { apiJson } from '@/lib/api'
import type {
  AcademicSummary, Curriculum, ExamItem, Finance, Grade, Internship, Profile, ScheduleItem,
} from '@/types/student'

const useStudentQuery = <T,>(path: string) =>
  useQuery({ queryKey: ['students', 'me', path], queryFn: () => apiJson<T>(`/students/me${path}`) })

export const useProfile = () => useStudentQuery<Profile>('')
export const useCurriculum = () => useStudentQuery<Curriculum>('/curriculum')
export const useSchedule = () => useStudentQuery<ScheduleItem[]>('/schedule')
export const useExams = () => useStudentQuery<ExamItem[]>('/exams')
export const useInternships = () => useStudentQuery<Internship[]>('/internships')
export const useGrades = () => useStudentQuery<Grade[]>('/grades')
export const useAcademicSummary = () => useStudentQuery<AcademicSummary>('/academic-summary')
export const useFinance = () => useStudentQuery<Finance>('/finance')
