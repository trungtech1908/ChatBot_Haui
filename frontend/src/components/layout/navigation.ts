import type { LucideIcon } from 'lucide-react'
import {
  BookOpen, Briefcase, CalendarClock, CalendarDays, GraduationCap, LayoutDashboard, LineChart, Sparkles, UserRound,
  Wallet,
} from 'lucide-react'

export interface NavItem {
  to: string
  label: string
  icon: LucideIcon
}

export interface NavSection {
  title: string
  items: NavItem[]
}

export const navigation: NavSection[] = [
  {
    title: 'Tổng quan',
    items: [
      { to: '/', label: 'Trang chủ', icon: LayoutDashboard },
      { to: '/profile', label: 'Hồ sơ sinh viên', icon: UserRound },
    ],
  },
  {
    title: 'Học tập',
    items: [
      { to: '/curriculum', label: 'Chương trình đào tạo', icon: BookOpen },
      { to: '/schedule', label: 'Lịch học', icon: CalendarDays },
      { to: '/exams', label: 'Lịch thi', icon: CalendarClock },
      { to: '/grades', label: 'Kết quả học tập', icon: LineChart },
      { to: '/academic-summary', label: 'Tổng kết & tốt nghiệp', icon: GraduationCap },
    ],
  },
  {
    title: 'Khác',
    items: [
      { to: '/internship', label: 'Thực tập', icon: Briefcase },
      { to: '/finance', label: 'Tài chính', icon: Wallet },
    ],
  },
]

export const assistantItem: NavItem = { to: '/chat', label: 'Trợ lý AI', icon: Sparkles }

export const findNavItem = (pathname: string) =>
  [...navigation.flatMap((s) => s.items), assistantItem].find((item) => item.to === pathname)
