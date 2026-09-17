import type { LucideIcon } from 'lucide-react'
import {
  BookOpen, Bot, Briefcase, Calendar, ChartLine, ClipboardList, History, IdCard, Medal, Wallet,
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
      { to: '/profile', label: 'Hồ sơ Sinh viên', icon: IdCard },
      { to: '/curriculum', label: 'Chương trình Đào tạo', icon: BookOpen },
      { to: '/schedule', label: 'Lịch Học', icon: Calendar },
      { to: '/exams', label: 'Lịch Thi', icon: ClipboardList },
      { to: '/internship', label: 'Thực tập Doanh nghiệp', icon: Briefcase },
    ],
  },
  {
    items: [
      { to: '/grades', label: 'Kết Quả Môn Học', icon: ChartLine },
      { to: '/academic-summary', label: 'Tổng Kết Học Kỳ & TN', icon: Medal },
    ],
  },
  {
    title: 'Tài chính',
    items: [
      { to: '/finance', label: 'Tài Chính & Công nợ', icon: Wallet },
      { to: '/transactions', label: 'Lịch Sử Giao Dịch', icon: History },
    ],
  },
  {
    title: 'Công cụ',
    items: [{ to: '/chat', label: 'Trợ lý ảo', icon: Bot }],
  },
]
