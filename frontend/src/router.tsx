import { createBrowserRouter, Navigate } from 'react-router'

import { AppLayout } from '@/components/layout/AppLayout'
import { AcademicSummaryPage } from '@/features/academic/AcademicSummaryPage'
import { LoginPage } from '@/features/auth/LoginPage'
import { RequireAuth } from '@/features/auth/RequireAuth'
import { CurriculumPage } from '@/features/curriculum/CurriculumPage'
import { ExamsPage } from '@/features/exams/ExamsPage'
import { FinancePage } from '@/features/finance/FinancePage'
import { GradesPage } from '@/features/grades/GradesPage'
import { InternshipPage } from '@/features/internship/InternshipPage'
import { OverviewPage } from '@/features/overview/OverviewPage'
import { ProfilePage } from '@/features/profile/ProfilePage'
import { SchedulePage } from '@/features/schedule/SchedulePage'

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    path: '/',
    element: (
      <RequireAuth>
        <AppLayout />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <OverviewPage /> },
      { path: 'profile', element: <ProfilePage /> },
      { path: 'curriculum', element: <CurriculumPage /> },
      { path: 'schedule', element: <SchedulePage /> },
      { path: 'exams', element: <ExamsPage /> },
      { path: 'internship', element: <InternshipPage /> },
      { path: 'grades', element: <GradesPage /> },
      { path: 'academic-summary', element: <AcademicSummaryPage /> },
      { path: 'finance', element: <FinancePage /> },
      { path: 'transactions', element: <Navigate to="/finance" replace /> },
      // Tách bundle: trang chat kéo theo thư viện markdown. Một route cho cả cuộc mới và cuộc có sẵn:
      // tạo cuộc mới khi đang stream chỉ đổi URL, không remount trang (không cắt stream)
      { path: 'chat/:conversationId?', lazy: () => import('@/features/chat/ChatPage').then((m) => ({ Component: m.ChatPage })) },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])
