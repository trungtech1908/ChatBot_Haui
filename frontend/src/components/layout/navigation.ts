export interface NavItem {
  to: string
  label: string
}

export interface NavSection {
  title: string
  items: NavItem[]
}

export const navigation: NavSection[] = [
  {
    title: 'Chung',
    items: [
      { to: '/', label: 'Tổng quan' },
      { to: '/profile', label: 'Hồ sơ sinh viên' },
    ],
  },
  {
    title: 'Học tập',
    items: [
      { to: '/curriculum', label: 'Chương trình đào tạo' },
      { to: '/schedule', label: 'Thời khóa biểu' },
      { to: '/exams', label: 'Lịch thi' },
      { to: '/grades', label: 'Kết quả học tập' },
      { to: '/academic-summary', label: 'Tổng kết & tốt nghiệp' },
      { to: '/internship', label: 'Thực tập' },
    ],
  },
  {
    title: 'Tài chính',
    items: [{ to: '/finance', label: 'Học phí & giao dịch' }],
  },
  {
    title: 'Hỗ trợ',
    items: [{ to: '/chat', label: 'Hỏi đáp quy chế' }],
  },
]
