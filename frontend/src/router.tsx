import { createBrowserRouter, Navigate } from 'react-router'

import { AppLayout } from '@/components/layout/AppLayout'
import { AcademicSummaryPage } from '@/features/academic/AcademicSummaryPage'
import { LoginPage } from '@/features/auth/LoginPage'
import { RequireAuth } from '@/features/auth/RequireAuth'
import { ChatPage } from '@/features/chat/ChatPage'
import { CurriculumPage } from '@/features/curriculum/CurriculumPage'
import { ExamsPage } from '@/features/exams/ExamsPage'
import { FinancePage } from '@/features/finance/FinancePage'
import { TransactionsPage } from '@/features/finance/TransactionsPage'
import { GradesPage } from '@/features/grades/GradesPage'
import { InternshipPage } from '@/features/internship/InternshipPage'
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
      { index: true, element: <Navigate to="/profile" replace /> },
      { path: 'profile', element: <ProfilePage /> },
      { path: 'curriculum', element: <CurriculumPage /> },
      { path: 'schedule', element: <SchedulePage /> },
      { path: 'exams', element: <ExamsPage /> },
      { path: 'internship', element: <InternshipPage /> },
      { path: 'grades', element: <GradesPage /> },
      { path: 'academic-summary', element: <AcademicSummaryPage /> },
      { path: 'finance', element: <FinancePage /> },
      { path: 'transactions', element: <TransactionsPage /> },
      { path: 'chat', element: <ChatPage /> },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])
