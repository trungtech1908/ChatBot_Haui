export interface Policy {
  ethnicity: string | null
  nationality: string | null
  poorHousehold: boolean
  nearPoorHousehold: boolean
  orphan: boolean
  disabled: boolean
}

export interface Profile {
  studentId: string
  username: string
  fullName: string | null
  email: string | null
  dateOfBirth: string | null
  phone: string | null
  address: string | null
  major: string | null
  cohort: string | null
  faculty: string | null
  policy: Policy | null
}

export interface CurriculumCourse {
  code: string
  name: string
  credits: number
  semester: number | null
}

export interface CurriculumGroup {
  code: string
  name: string | null
  type: string | null
  requiredCredits: number | null
  courses: CurriculumCourse[]
}

export interface Curriculum {
  major: string
  cohort: string
  requiredCredits: number | null
  groups: CurriculumGroup[]
}

export interface ScheduleItem {
  semester: string
  courseName: string | null
  classCode: string
  weekday: number | null
  periods: string | null
  weeks: string | null
  room: string | null
  lecturer: string | null
}

export interface ExamItem {
  semester: string
  courseName: string | null
  candidateNumber: number
  examCode: string | null
  startTime: string | null
  durationMinutes: number | null
  room: string | null
  seat: string | null
  format: string | null
  eligible: boolean
  ineligibleReason: string | null
}

export interface Internship {
  semester: string
  company: string | null
  position: string | null
  address: string | null
  field: string | null
  supervisor: string | null
  companyEmail: string | null
  startDate: string | null
  endDate: string | null
  status: string
  score: number | null
}

export interface Grade {
  semester: string
  semesterCode: string
  courseCode: string | null
  courseName: string | null
  credits: number
  /** Lần học: 1 = lần đầu */
  attempt: number
  /** Điểm quá trình */
  process: number | null
  /** Điểm thi */
  exam: number | null
  /** Điểm học phần hệ 10 */
  total: number | null
  letter: string | null
  /** Lần học dùng tính điểm tích lũy */
  official: boolean
}

export interface SemesterSummary {
  code: string
  semester: string
  gpa: number | null
  cumulativeGpa: number | null
  credits: number | null
  courseCount: number
  conductScore: number | null
  warning: boolean
}

export interface Graduation {
  gpa: number | null
  /** Tín chỉ tích lũy */
  credits: number
  creditsOk: boolean
  physicalEducationOk: boolean
  languageOk: boolean
  defenseEducationOk: boolean
}

export interface AcademicSummary {
  semesters: SemesterSummary[]
  graduation: Graduation | null
}

export interface Transaction {
  code: string
  time: string
  name: string | null
  note: string | null
  amount: number | null
  isIncome: boolean
  status: string
}

export interface Finance {
  balance: number
  debt: number
  scholarship: number
  transactions: Transaction[]
}
