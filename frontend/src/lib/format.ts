import type { Tone } from '@/types/ui'

const currency = new Intl.NumberFormat('vi-VN')

export const formatMoney = (value: number | null | undefined) => (value == null ? '—' : `${currency.format(value)} đ`)

/** Số tiền gọn cho ô số liệu: 12,5 tr / 950 N */
export function formatMoneyShort(value: number) {
  const abs = Math.abs(value)
  if (abs >= 1e9) return `${(value / 1e9).toLocaleString('vi-VN', { maximumFractionDigits: 1 })} tỷ`
  if (abs >= 1e6) return `${(value / 1e6).toLocaleString('vi-VN', { maximumFractionDigits: 1 })} tr`
  if (abs >= 1e3) return `${Math.round(value / 1e3).toLocaleString('vi-VN')} N`
  return `${value}`
}

export const formatDate = (value: string | null | undefined) =>
  value ? new Date(value).toLocaleDateString('vi-VN') : '—'

export const formatDateTime = (value: string | null | undefined) =>
  value
    ? new Date(value).toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit', year: 'numeric' })
    : '—'

export const formatTime = (value: string) =>
  new Date(value).toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })

export const formatClock = (value: string | null | undefined) =>
  value ? new Date(value).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) : '—'

export const score = (value: number | null | undefined, digits = 1) => (value == null ? '—' : value.toFixed(digits))

/** 'Học kỳ 2 năm học 2025-2026' → 'HK2 2025-2026'; 'Học kỳ phụ hè năm học 2025-2026' → 'Hè 2025-2026' */
export function shortSemester(name: string | null | undefined) {
  if (!name) return '—'
  const year = name.match(/\d{4}-\d{4}/)?.[0] ?? ''
  if (/phụ|hè/i.test(name)) return `Hè ${year}`.trim()
  const n = name.match(/Học kỳ (\d)/)?.[1]
  return n ? `HK${n} ${year}`.trim() : name
}

const CLASSIFICATION: Record<string, { label: string; tone: Tone }> = {
  xuat_sac: { label: 'Xuất sắc', tone: 'green' },
  gioi: { label: 'Giỏi', tone: 'blue' },
  tot: { label: 'Tốt', tone: 'blue' },
  kha: { label: 'Khá', tone: 'yellow' },
  trung_binh: { label: 'Trung bình', tone: 'orange' },
  yeu: { label: 'Yếu', tone: 'red' },
  kem: { label: 'Kém', tone: 'red' },
}

/** Xếp loại học lực / rèn luyện từ mã (xuat_sac, gioi, tot...). */
export const classification = (code: string | null | undefined) =>
  (code && CLASSIFICATION[code]) || { label: '—', tone: 'gray' as Tone }

/** Xếp loại học lực theo điểm TBC hệ 4. */
export function classifyGpa(gpa: number | null): { label: string; tone: Tone } {
  if (gpa == null) return { label: '—', tone: 'gray' }
  if (gpa >= 3.6) return { label: 'Xuất sắc', tone: 'green' }
  if (gpa >= 3.2) return { label: 'Giỏi', tone: 'blue' }
  if (gpa >= 2.5) return { label: 'Khá', tone: 'yellow' }
  if (gpa >= 2.0) return { label: 'Trung bình', tone: 'orange' }
  return { label: 'Yếu', tone: 'red' }
}

export function letterTone(letter: string | null): Tone {
  const key = letter?.[0]
  return key === 'A' ? 'green' : key === 'B' ? 'blue' : key === 'C' ? 'yellow' : key === 'D' ? 'orange' : key === 'F' ? 'red' : 'gray'
}

export const REGISTRATION: Record<string, string> = {
  lan_dau: 'Lần đầu',
  hoc_lai: 'Học lại',
  cai_thien: 'Cải thiện',
  hoc_doi: 'Học đổi',
}

export const weekdayLabel = (weekday: number | null) => (weekday == null ? '—' : weekday >= 8 || weekday === 1 ? 'Chủ nhật' : `Thứ ${weekday}`)

export const formatPeriods = (periods: string | null) => periods?.replace(/^Tiet/i, 'Tiết') ?? '—'

/** Thứ trong tuần theo quy ước lịch học (2..7 = thứ Hai..thứ Bảy, 8 = Chủ nhật) của ngày hôm nay */
export const todayWeekday = () => {
  const d = new Date().getDay()
  return d === 0 ? 8 : d + 1
}

/** Khoảng cách tới một thời điểm, dạng "còn 3 ngày" / "2 ngày trước" */
export function relativeDays(value: string) {
  const days = Math.round((new Date(value).setHours(0, 0, 0, 0) - new Date().setHours(0, 0, 0, 0)) / 86_400_000)
  if (days === 0) return 'hôm nay'
  if (days === 1) return 'ngày mai'
  return days > 0 ? `còn ${days} ngày` : `${-days} ngày trước`
}

export const isOverdue = (dueDate: string | null, remaining: number) =>
  remaining > 0 && !!dueDate && new Date(dueDate) < new Date(new Date().toDateString())

/** Mã học kỳ '20251' → 'HK1 2025-2026'; hậu tố 3 là học kỳ phụ hè */
export function semesterFromCode(code: string | null | undefined) {
  if (!code || code.length !== 5) return code ?? '—'
  const y = Number(code.slice(0, 4))
  const n = code[4]
  return `${n === '3' ? 'Hè' : `HK${n}`} ${y}-${y + 1}`
}
