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
  courseName: string | null
  classCode: string
  weekday: number | null
  periods: string | null
  room: number | null
  lecturer: string | null
}

export interface ExamItem {
  candidateNumber: number
  examCode: string | null
  startTime: string | null
  room: number | null
  seat: string | null
  format: string | null
  eligible: boolean
}

export interface Internship {
  company: string | null
  position: string | null
  address: string | null
  supervisor: string | null
  companyEmail: string | null
}

export interface Grade {
  courseCode: string | null
  courseName: string | null
  tx1: number | null
  tx2: number | null
  midterm: number | null
  final: number | null
  total: number | null
  letter: string | null
}

export interface SemesterSummary {
  semester: number | null
  gpa: number | null
  credits: number | null
  courseCount: number
}

export interface Graduation {
  gpa: number | null
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
  name: string | null
  note: string | null
  amount: number | null
  isIncome: boolean
}

export interface Finance {
  balance: number
  debt: number
  scholarship: number
  transactions: Transaction[]
}
