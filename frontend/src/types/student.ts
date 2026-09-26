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

export type CourseStatus = 'da_dat' | 'chua_dat' | 'chua_co_diem' | 'chua_hoc'

export interface CurriculumCourse {
  code: string
  name: string
  credits: number
  /** Học kỳ thứ mấy theo kế hoạch chuẩn */
  semester: number | null
  status: CourseStatus
  /** Điểm chữ của lần học chính thức */
  letter: string | null
  /** Mã học kỳ đã học */
  takenSemester: string | null
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
  semesterCode: string
  startPeriod: number
  endPeriod: number
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
  semesterCode: string
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
  /** Điểm hệ 4 */
  grade4: number | null
  /** null: chưa có kết quả (I, X) */
  passed: boolean | null
  /** Có tính vào điểm trung bình không (GDTC, GDQP thì không) */
  countsGpa: boolean
  registration: 'lan_dau' | 'hoc_lai' | 'cai_thien' | 'hoc_doi' | null
  courseType: string
  /** Lần học dùng tính điểm tích lũy */
  official: boolean
}

export interface SemesterSummary {
  code: string
  semester: string
  gpa: number | null
  cumulativeGpa: number | null
  credits: number | null
  creditsRegistered: number | null
  creditsFailed: number | null
  cumulativeCredits: number | null
  classification: string | null
  courseCount: number
  conductScore: number | null
  conductClassification: string | null
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
  kind: string
  time: string
  name: string | null
  note: string | null
  amount: number | null
  isIncome: boolean
  status: string
}

export interface SemesterDebt {
  semesterCode: string
  semester: string
  total: number
  paid: number
  remaining: number
  dueDate: string | null
}

export interface Payable {
  id: number
  semesterCode: string
  semester: string
  kind: 'hoc_phi' | 'khoan_thu' | 'phi_phat' | 'khac'
  content: string | null
  amount: number
  paid: number
  remaining: number
  dueDate: string | null
}

export interface Finance {
  balance: number
  debt: number
  scholarship: number
  debts: SemesterDebt[]
  payables: Payable[]
  transactions: Transaction[]
}
