import { ArrowUpRight, CalendarClock, Check, Clock, Layers, MapPin, Minus, Receipt, TrendingUp } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router'

import { useAcademicSummary, useCurriculum, useExams, useFinance, useProfile, useSchedule } from '@/api/students'
import { LineChart } from '@/components/charts/LineChart'
import { Alert } from '@/components/ui/Alert'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { Progress } from '@/components/ui/Progress'
import { Section } from '@/components/ui/Section'
import { StatGrid } from '@/components/ui/StatCard'
import { cn } from '@/lib/cn'
import { classifyGpa, formatClock, formatDate, formatMoney, isOverdue, relativeDays, score, shortSemester, todayWeekday, weekdayLabel } from '@/lib/format'

const more = (to: string, label = 'Xem tất cả') => (
  <Link to={to} className="btn-ghost h-7 gap-1 px-2 text-[13px]">
    {label} <ArrowUpRight size={14} />
  </Link>
)

const Placeholder = ({ loading, children }: { loading: boolean; children: ReactNode }) => (
  <p className="px-5 py-8 text-center text-muted">{loading ? 'Đang tải…' : children}</p>
)

const today = new Date().toLocaleDateString('vi-VN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
const startOfToday = () => new Date(new Date().toDateString())

export function OverviewPage() {
  const profile = useProfile().data
  const summary = useAcademicSummary().data
  const curriculum = useCurriculum().data
  const finance = useFinance().data
  const schedule = useSchedule().data
  const exams = useExams().data

  const graduation = summary?.graduation
  const required = curriculum?.requiredCredits ?? 0
  const earned = graduation?.credits ?? 0
  const main = summary?.semesters.filter((s) => s.gpa != null || s.cumulativeGpa != null) ?? []
  const latest = summary?.semesters.at(-1)

  // Học kỳ hiện tại = học kỳ mới nhất có lịch học / lịch thi
  const scheduleTerm = schedule?.[0]?.semesterCode
  const todayClasses = (schedule ?? [])
    .filter((i) => i.semesterCode === scheduleTerm && (i.weekday === 1 ? 8 : i.weekday) === todayWeekday())
    .sort((a, b) => a.startPeriod - b.startPeriod)
  const upcomingExams = (exams ?? [])
    .filter((e) => e.startTime && new Date(e.startTime) >= startOfToday())
    .sort((a, b) => a.startTime!.localeCompare(b.startTime!))
  const overdue = finance?.payables.filter((p) => isOverdue(p.dueDate, p.remaining)) ?? []
  const banned = upcomingExams.filter((e) => !e.eligible)

  const conditions = graduation
    ? ([
        ['Đủ tín chỉ', graduation.creditsOk],
        ['GDTC', graduation.physicalEducationOk],
        ['GDQP-AN', graduation.defenseEducationOk],
        ['Ngoại ngữ', graduation.languageOk],
      ] as const)
    : []

  return (
    <>
      <PageHeader title={profile ? `Xin chào, ${profile.fullName}` : 'Tổng quan'} description={<span className="first-letter:uppercase">{today}</span>} />

      <div className="space-y-6">
        {(overdue.length > 0 || banned.length > 0 || latest?.warning) && (
          <div className="space-y-2">
            {overdue.length > 0 && (
              <Alert tone="danger" title={`Quá hạn nộp ${formatMoney(overdue.reduce((s, p) => s + p.remaining, 0))}`} action={more('/finance', 'Xem công nợ')}>
                {overdue.length} khoản chưa nộp đã quá hạn.
              </Alert>
            )}
            {banned.length > 0 && (
              <Alert tone="danger" title={`Bị cấm thi ${banned.length} học phần`} action={more('/exams', 'Xem lịch thi')}>
                {banned.map((e) => e.courseName).join(', ')}
              </Alert>
            )}
            {latest?.warning && <Alert tone="warning" title={`Cảnh báo học tập ${latest.semester}`} action={more('/academic-summary', 'Xem kết quả')} />}
          </div>
        )}

        <StatGrid
          items={[
            { label: 'GPA tích lũy', value: score(graduation?.gpa, 2), note: graduation ? `Thang 4 · ${classifyGpa(graduation.gpa).label}` : undefined, icon: TrendingUp, trend: main.map((s) => s.cumulativeGpa) },
            { label: 'Tín chỉ tích lũy', value: summary ? (required ? `${earned} / ${required}` : earned) : '—', note: required ? `${Math.round((earned / required) * 100)}% chương trình` : undefined, icon: Layers, trend: main.map((s) => s.cumulativeCredits) },
            { label: 'Công nợ học phí', value: finance ? formatMoney(finance.debt) : '—', note: finance ? (finance.debt ? (overdue.length ? 'Có khoản quá hạn' : 'Chưa đến hạn') : 'Không có công nợ') : undefined, icon: Receipt, alert: !!finance?.debt },
            { label: 'Môn thi sắp tới', value: exams ? upcomingExams.length : '—', note: upcomingExams[0] ? `${upcomingExams[0].courseName} · ${relativeDays(upcomingExams[0].startTime!)}` : 'Không có lịch thi sắp tới', icon: CalendarClock },
          ]}
        />

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
          <Section title="Điểm trung bình" description="Thang điểm 4" aside={more('/academic-summary')}>
            {main.length ? (
              <LineChart
                categories={main.map((s) => shortSemester(s.semester))}
                series={[
                  { name: 'TB học kỳ', color: 'var(--chart-1)', values: main.map((s) => s.gpa) },
                  { name: 'TB tích lũy', color: 'var(--chart-2)', values: main.map((s) => s.cumulativeGpa) },
                ]}
                domain={[0, 4]}
                ticks={[0, 1, 2, 3, 4]}
                height={220}
                label="Điểm trung bình học kỳ và tích lũy theo học kỳ"
              />
            ) : (
              <Placeholder loading={!summary}>Chưa có học kỳ nào được tổng kết.</Placeholder>
            )}
          </Section>

          <Section title="Tiến độ tốt nghiệp" aside={more('/academic-summary', 'Chi tiết')}>
            {graduation ? (
              <div className="space-y-5">
                <div>
                  <div className="mb-2 flex items-baseline justify-between text-[13px]">
                    <span className="text-muted">Tín chỉ tích lũy</span>
                    <span className="font-semibold tabular-nums">{earned}/{required || '—'}</span>
                  </div>
                  <Progress value={earned} max={required} />
                </div>
                <ul className="grid grid-cols-2 gap-2">
                  {conditions.map(([label, ok]) => (
                    <li key={label} className={cn('flex items-center gap-2 rounded-lg border px-3 py-2 text-[13px]', ok ? 'border-success/25 bg-success-soft' : 'border-line')}>
                      {ok ? <Check size={14} className="text-success" strokeWidth={3} /> : <Minus size={14} className="text-muted" strokeWidth={3} />}
                      <span className={ok ? 'font-medium' : 'text-muted'}>{label}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <Placeholder loading={!summary}>Chưa có dữ liệu.</Placeholder>
            )}
          </Section>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <Section title={`Lịch học hôm nay`} description={weekdayLabel(todayWeekday())} aside={more('/schedule', 'Thời khóa biểu')} flush>
            {todayClasses.length ? (
              <ul className="divide-y divide-line">
                {todayClasses.map((c) => (
                  <li key={`${c.classCode}-${c.startPeriod}`} className="flex gap-3 px-5 py-3">
                    <div className="w-1 shrink-0 rounded-full bg-brand" />
                    <div className="min-w-0">
                      <p className="truncate font-medium">{c.courseName}</p>
                      <p className="mt-0.5 flex flex-wrap gap-x-3 text-xs text-muted">
                        <span className="inline-flex items-center gap-1"><Clock size={12} />Tiết {c.startPeriod}–{c.endPeriod}</span>
                        <span className="inline-flex items-center gap-1"><MapPin size={12} />{c.room}</span>
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <Placeholder loading={!schedule}>Hôm nay không có lịch học.</Placeholder>
            )}
          </Section>

          <Section title="Lịch thi sắp tới" aside={more('/exams')} flush>
            {upcomingExams.length ? (
              <ul className="divide-y divide-line">
                {upcomingExams.slice(0, 4).map((exam) => {
                  const start = new Date(exam.startTime!)
                  return (
                    <li key={`${exam.examCode}-${exam.startTime}`} className="flex items-center gap-3 px-5 py-3">
                      <div className="flex h-11 w-11 shrink-0 flex-col items-center justify-center rounded-lg bg-brand-soft leading-none text-brand-ink">
                        <span className="text-[10px] font-medium uppercase">Th{start.getMonth() + 1}</span>
                        <span className="mt-0.5 font-semibold tabular-nums">{start.getDate()}</span>
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-medium">{exam.courseName}</p>
                        <p className="truncate text-xs text-muted">{formatClock(exam.startTime)} · Phòng {exam.room} · SBD {exam.candidateNumber}</p>
                      </div>
                      {exam.eligible ? <span className="shrink-0 text-xs text-brand-ink">{relativeDays(exam.startTime!)}</span> : <Badge variant="soft" tone="red">Cấm thi</Badge>}
                    </li>
                  )
                })}
              </ul>
            ) : (
              <Placeholder loading={!exams}>Không có lịch thi sắp tới.</Placeholder>
            )}
          </Section>

          <Section title="Giao dịch gần đây" aside={more('/finance')} flush>
            {finance?.transactions.length ? (
              <ul className="divide-y divide-line">
                {finance.transactions.slice(0, 5).map((t) => (
                  <li key={t.code} className="flex items-center justify-between gap-3 px-5 py-3">
                    <div className="min-w-0">
                      <p className="truncate font-medium">{t.name}</p>
                      <p className="truncate text-xs text-muted">{formatDate(t.time)}</p>
                    </div>
                    <span className={cn('shrink-0 font-semibold tabular-nums', t.isIncome && 'text-success')}>
                      {t.isIncome ? '+' : '−'}{formatMoney(t.amount)}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <Placeholder loading={!finance}>Chưa có giao dịch.</Placeholder>
            )}
          </Section>
        </div>
      </div>
    </>
  )
}
