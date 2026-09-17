import { ArrowUpRight } from 'lucide-react'
import { Link } from 'react-router'

import { useAcademicSummary, useCurriculum, useExams, useFinance, useProfile, useSchedule } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { Figures } from '@/components/ui/Figures'
import { PageHeader } from '@/components/ui/PageHeader'
import { Progress } from '@/components/ui/Progress'
import { Section } from '@/components/ui/Section'
import { formatMoney, formatPeriods, weekdayLabel } from '@/lib/format'

const more = (to: string) => (
  <Link to={to} className="btn-ghost h-7 gap-1 px-2 text-[13px]">
    Xem tất cả <ArrowUpRight size={14} />
  </Link>
)

const today = new Date().toLocaleDateString('vi-VN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })

export function OverviewPage() {
  const profile = useProfile().data
  const summary = useAcademicSummary().data
  const curriculum = useCurriculum().data
  const finance = useFinance().data
  const schedule = useSchedule().data
  const exams = useExams().data

  const graduation = summary?.graduation
  const conditions = graduation
    ? [graduation.creditsOk, graduation.physicalEducationOk, graduation.defenseEducationOk, graduation.languageOk]
    : []
  const doneConditions = conditions.filter(Boolean).length
  const earnedCredits = summary?.semesters.reduce((sum, s) => sum + (s.credits ?? 0), 0) ?? 0

  return (
    <>
      <PageHeader title={profile ? `Xin chào, ${profile.fullName}` : 'Tổng quan'} description={<span className="first-letter:uppercase">{today}</span>} />

      <div className="space-y-4">
        <Figures
          items={[
            { label: 'GPA tích lũy', value: graduation?.gpa ?? '—', note: 'Thang điểm 4' },
            { label: 'Tín chỉ đã tích lũy', value: summary ? earnedCredits : '—', note: curriculum ? `Yêu cầu ${curriculum.requiredCredits} tín chỉ` : undefined },
            { label: 'Công nợ học phí', value: finance ? formatMoney(finance.debt) : '—', alert: !!finance?.debt, note: finance?.debt ? 'Cần nộp trước hạn' : 'Không có công nợ' },
            { label: 'Số dư tài khoản', value: finance ? formatMoney(finance.balance) : '—' },
          ]}
        />

        <div className="grid gap-4 lg:grid-cols-3">
          <Section title="Lịch học trong tuần" description={schedule ? `${schedule.length} buổi học` : undefined} aside={more('/schedule')} flush className="lg:col-span-2">
            {schedule?.length ? (
              <ul className="divide-y divide-line">
                {[...schedule].sort((a, b) => (a.weekday ?? 0) - (b.weekday ?? 0)).map((item, i) => (
                  <li key={i} className="flex items-center gap-4 px-5 py-3">
                    <div className="w-20 shrink-0">
                      <p className="font-medium">{weekdayLabel(item.weekday)}</p>
                      <p className="text-xs text-muted">{formatPeriods(item.periods)}</p>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium">{item.courseName}</p>
                      <p className="truncate text-[13px] text-muted">{item.lecturer}</p>
                    </div>
                    <span className="shrink-0 rounded-md bg-hover px-2 py-1 text-xs font-medium tabular-nums">P.{item.room}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="px-5 py-8 text-center text-muted">{schedule ? 'Chưa có lịch học.' : 'Đang tải…'}</p>
            )}
          </Section>

          <Section title="Tiến độ tốt nghiệp" aside={more('/academic-summary')}>
            {graduation ? (
              <div className="space-y-5">
                <div>
                  <div className="mb-2 flex items-baseline justify-between">
                    <span className="text-[13px] text-muted">Tín chỉ</span>
                    <span className="text-[13px] font-medium tabular-nums">
                      {earnedCredits}/{curriculum?.requiredCredits ?? '—'}
                    </span>
                  </div>
                  <Progress value={earnedCredits} max={curriculum?.requiredCredits ?? 0} />
                </div>
                <div>
                  <div className="mb-2 flex items-baseline justify-between">
                    <span className="text-[13px] text-muted">Điều kiện tốt nghiệp</span>
                    <span className="text-[13px] font-medium tabular-nums">{doneConditions}/4</span>
                  </div>
                  <Progress value={doneConditions} max={4} />
                </div>
                <div className="flex flex-wrap gap-1.5">
                  <Badge tone={graduation.physicalEducationOk ? 'green' : 'gray'}>GDTC</Badge>
                  <Badge tone={graduation.defenseEducationOk ? 'green' : 'gray'}>GDQP</Badge>
                  <Badge tone={graduation.languageOk ? 'green' : 'gray'}>Ngoại ngữ</Badge>
                </div>
              </div>
            ) : (
              <p className="py-6 text-center text-muted">{summary ? 'Chưa có dữ liệu.' : 'Đang tải…'}</p>
            )}
          </Section>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Section title="Lịch thi" aside={more('/exams')} flush>
            {exams?.length ? (
              <ul className="divide-y divide-line">
                {[...exams].sort((a, b) => (a.startTime ?? '').localeCompare(b.startTime ?? '')).slice(0, 4).map((exam) => {
                  const start = exam.startTime ? new Date(exam.startTime) : null
                  return (
                    <li key={exam.candidateNumber} className="flex items-center gap-4 px-5 py-3">
                      <div className="flex h-11 w-11 shrink-0 flex-col items-center justify-center rounded-lg border border-line bg-surface-2 leading-none">
                        <span className="text-[10px] text-muted uppercase">Th{start ? start.getMonth() + 1 : '—'}</span>
                        <span className="mt-0.5 font-semibold tabular-nums">{start?.getDate() ?? '—'}</span>
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="font-medium">
                          {start?.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })} · Phòng {exam.room}
                        </p>
                        <p className="text-[13px] text-muted">
                          {exam.format} · SBD {exam.candidateNumber}
                        </p>
                      </div>
                      {!exam.eligible && <Badge tone="red">Không đủ ĐK</Badge>}
                    </li>
                  )
                })}
              </ul>
            ) : (
              <p className="px-5 py-8 text-center text-muted">{exams ? 'Chưa có lịch thi.' : 'Đang tải…'}</p>
            )}
          </Section>

          <Section title="Giao dịch gần đây" aside={more('/finance')} flush>
            {finance?.transactions.length ? (
              <ul className="divide-y divide-line">
                {finance.transactions.slice(0, 4).map((t) => (
                  <li key={t.code} className="flex items-center justify-between gap-4 px-5 py-3">
                    <div className="min-w-0">
                      <p className="truncate font-medium">{t.name}</p>
                      <p className="truncate text-[13px] text-muted">{t.note}</p>
                    </div>
                    <span className={t.isIncome ? 'shrink-0 font-medium text-success tabular-nums' : 'shrink-0 font-medium tabular-nums'}>
                      {t.isIncome ? '+' : '−'}
                      {formatMoney(t.amount)}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="px-5 py-8 text-center text-muted">{finance ? 'Chưa có giao dịch.' : 'Đang tải…'}</p>
            )}
          </Section>
        </div>
      </div>
    </>
  )
}
