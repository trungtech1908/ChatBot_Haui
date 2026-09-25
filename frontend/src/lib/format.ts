import type { Tone } from '@/types/ui'

const currency = new Intl.NumberFormat('vi-VN')

export const formatMoney = (value: number | null | undefined) => (value == null ? '—' : `${currency.format(value)} đ`)

export const formatDate = (value: string | null | undefined) =>
  value ? new Date(value).toLocaleDateString('vi-VN') : '—'

export const formatDateTime = (value: string | null | undefined) =>
  value
    ? new Date(value).toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit', year: 'numeric' })
    : '—'

export const formatTime = (value: string) =>
  new Date(value).toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })

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


export const weekdayLabel = (weekday: number | null) => (weekday == null ? '—' : weekday >= 8 || weekday === 1 ? 'Chủ nhật' : `Thứ ${weekday}`)

export const formatPeriods = (periods: string | null) => periods?.replace(/^Tiet/i, 'Tiết') ?? '—'
