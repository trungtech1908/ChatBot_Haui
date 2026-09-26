import type { LucideIcon } from 'lucide-react'
import {
  BookOpen, Briefcase, CalendarDays, ClipboardCheck, GraduationCap, House, LineChart, MessageSquareText, UserRound, Wallet,
} from 'lucide-react'

export interface NavItem {
  to: string
  label: string
  icon: LucideIcon
}

export interface NavSection {
  title?: string
  items: NavItem[]
}

export const navigation: NavSection[] = [
  {
    items: [
      { to: '/', label: 'Tổng quan', icon: House },
      { to: '/profile', label: 'Hồ sơ', icon: UserRound },
    ],
  },
  {
    title: 'Học tập',
    items: [
      { to: '/schedule', label: 'Thời khóa biểu', icon: CalendarDays },
      { to: '/exams', label: 'Lịch thi', icon: ClipboardCheck },
      { to: '/grades', label: 'Kết quả học tập', icon: LineChart },
      { to: '/curriculum', label: 'Chương trình đào tạo', icon: BookOpen },
      { to: '/academic-summary', label: 'Tiến độ & tốt nghiệp', icon: GraduationCap },
      { to: '/internship', label: 'Thực tập', icon: Briefcase },
    ],
  },
  {
    title: 'Khác',
    items: [
      { to: '/finance', label: 'Học phí', icon: Wallet },
      { to: '/chat', label: 'Hỏi đáp quy chế', icon: MessageSquareText },
    ],
  },
]

export const findNavItem = (pathname: string) => navigation.flatMap((s) => s.items).find((item) => item.to === pathname)
