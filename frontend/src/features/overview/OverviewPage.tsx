import {
  ArrowRight, BookOpen, CalendarClock, CalendarDays, CircleDollarSign, GraduationCap, Sparkles, TrendingUp,
} from 'lucide-react'
import { Link } from 'react-router'

import { useAcademicSummary, useCurriculum, useExams, useFinance, useProfile, useSchedule } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { StatCard } from '@/components/ui/StatCard'
import { formatDateTime, formatMoney, formatPeriods, greeting } from '@/lib/format'

function Hero() {
  const { data: profile } = useProfile()
  return (
    <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-blue-600 via-indigo-600 to-violet-700 p-6 text-white shadow-lg shadow-indigo-500/20 md:p-8">
      <div className="pointer-events-none absolute -top-24 -right-16 h-72 w-72 rounded-full bg-white/10 blur-2xl" />
      <div className="relative flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm text-blue-100">{greeting()},</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight md:text-3xl">{profile ? profile.fullName : <Skeleton className="h-9 w-56 bg-white/20" />}</h1>
          <div className="mt-3 flex flex-wrap gap-2 text-sm">
            {profile?.major && <span className="rounded-full bg-white/15 px-3 py-1 ring-1 ring-white/20">{profile.major}</span>}
            {profile?.cohort && <span className="rounded-full bg-white/15 px-3 py-1 ring-1 ring-white/20">Khóa {profile.cohort}</span>}
            {profile?.studentId && <span className="rounded-full bg-white/15 px-3 py-1 font-mono ring-1 ring-white/20">{profile.studentId}</span>}
          </div>
        </div>
        <Link to="/chat" className="btn bg-white text-indigo-700 shadow-sm hover:bg-blue-50">
          <Sparkles size={16} /> Hỏi trợ lý AI
        </Link>
      </div>
    </div>
  )
}

function Stats() {
  const summary = useAcademicSummary().data
  const curriculum = useCurriculum().data
  const finance = useFinance().data
  const exams = useExams().data
  const upcoming = exams?.filter((e) => e.startTime && new Date(e.startTime) > new Date()).length

  return (
    <div className="grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
      <StatCard label="GPA tích lũy" value={summary?.graduation?.gpa ?? '---'} icon={TrendingUp} tone="blue" hint="Thang điểm 4" />
      <StatCard label="Tín chỉ yêu cầu" value={curriculum?.requiredCredits ?? '---'} icon={BookOpen} tone="purple" hint={curriculum?.major} />
      <StatCard
        label="Công nợ"
        value={finance ? formatMoney(finance.debt) : '---'}
        icon={CircleDollarSign}
        tone={finance?.debt ? 'red' : 'green'}
        hint={finance?.debt ? 'Cần thanh toán' : 'Không có công nợ'}
      />
      <StatCard label="Lịch thi sắp tới" value={exams ? upcoming : '---'} icon={CalendarClock} tone="orange" hint={`Tổng ${exams?.length ?? 0} ca thi`} />
    </div>
  )
}

const viewAll = (to: string) => (
  <Link to={to} className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline">
    Xem tất cả <ArrowRight size={14} />
  </Link>
)

function WeekSchedule() {
  const { data, isPending } = useSchedule()
  const items = [...(data ?? [])].sort((a, b) => (a.weekday ?? 0) - (b.weekday ?? 0)).slice(0, 5)
  return (
    <Card title="Lịch học trong tuần" icon={CalendarDays} action={viewAll('/schedule')} bodyClassName="p-2">
      {isPending ? (
        <Skeleton className="m-3 h-40" />
      ) : items.length ? (
        <ul>
          {items.map((item, i) => (
            <li key={i} className="flex items-center gap-4 rounded-xl p-3 transition hover:bg-surface-2">
              <div className="flex h-12 w-14 shrink-0 flex-col items-center justify-center rounded-xl bg-primary-soft text-primary">
                <span className="text-[10px] font-semibold uppercase">{item.weekday && item.weekday < 8 ? 'Thứ' : ''}</span>
                <span className="text-sm leading-none font-bold">{item.weekday && item.weekday < 8 ? item.weekday : 'CN'}</span>
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{item.courseName}</p>
                <p className="truncate text-sm text-muted">
                  {formatPeriods(item.periods)} · Phòng {item.room} · {item.lecturer}
                </p>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="p-4 text-sm text-muted">Chưa có lịch học.</p>
      )}
    </Card>
  )
}

function UpcomingExams() {
  const { data, isPending } = useExams()
  const items = [...(data ?? [])].sort((a, b) => (a.startTime ?? '').localeCompare(b.startTime ?? '')).slice(0, 4)
  return (
    <Card title="Lịch thi" icon={GraduationCap} action={viewAll('/exams')} bodyClassName="p-2">
      {isPending ? (
        <Skeleton className="m-3 h-40" />
      ) : items.length ? (
        <ul>
          {items.map((exam) => (
            <li key={exam.candidateNumber} className="flex items-center justify-between gap-3 rounded-xl p-3 transition hover:bg-surface-2">
              <div className="min-w-0">
                <p className="font-medium">{formatDateTime(exam.startTime)}</p>
                <p className="truncate text-sm text-muted">
                  Phòng {exam.room} · Ghế {exam.seat} · {exam.format}
                </p>
              </div>
              {exam.eligible ? <Badge tone="green">Đủ điều kiện</Badge> : <Badge tone="red">Không đủ ĐK</Badge>}
            </li>
          ))}
        </ul>
      ) : (
        <p className="p-4 text-sm text-muted">Chưa có lịch thi.</p>
      )}
    </Card>
  )
}

function RecentTransactions() {
  const { data, isPending } = useFinance()
  return (
    <Card title="Giao dịch gần đây" icon={CircleDollarSign} action={viewAll('/finance')} bodyClassName="p-2">
      {isPending ? (
        <Skeleton className="m-3 h-40" />
      ) : data?.transactions.length ? (
        <ul>
          {data.transactions.slice(0, 4).map((t) => (
            <li key={t.code} className="flex items-center justify-between gap-3 rounded-xl p-3 transition hover:bg-surface-2">
              <div className="min-w-0">
                <p className="truncate font-medium">{t.name}</p>
                <p className="truncate text-sm text-muted">{t.note}</p>
              </div>
              <span className={t.isIncome ? 'font-semibold text-emerald-600 tabular-nums dark:text-emerald-400' : 'font-semibold tabular-nums'}>
                {t.isIncome ? '+' : '−'}
                {formatMoney(t.amount)}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="p-4 text-sm text-muted">Chưa có giao dịch.</p>
      )}
    </Card>
  )
}

export function OverviewPage() {
  return (
    <div className="space-y-6">
      <Hero />
      <Stats />
      <div className="grid gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <WeekSchedule />
        </div>
        <UpcomingExams />
      </div>
      <RecentTransactions />
    </div>
  )
}

