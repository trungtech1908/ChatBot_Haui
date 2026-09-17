import { BarChart3, CheckCircle2, CircleDashed, GraduationCap } from 'lucide-react'

import { useAcademicSummary } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { cn } from '@/lib/cn'
import { classifyGpa } from '@/lib/format'
import type { Graduation, SemesterSummary } from '@/types/student'

function GpaRing({ gpa }: { gpa: number | null }) {
  const radius = 52
  const circumference = 2 * Math.PI * radius
  const progress = Math.min((gpa ?? 0) / 4, 1)
  return (
    <div className="relative h-36 w-36 shrink-0">
      <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
        <circle cx="60" cy="60" r={radius} fill="none" strokeWidth="10" className="stroke-surface-2" />
        <circle
          cx="60" cy="60" r={radius} fill="none" strokeWidth="10" strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={circumference * (1 - progress)}
          className="stroke-primary transition-[stroke-dashoffset] duration-700"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold tabular-nums">{gpa ?? '—'}</span>
        <span className="text-xs text-muted">/ 4.0</span>
      </div>
    </div>
  )
}

function GraduationPanel({ graduation }: { graduation: Graduation }) {
  const requirements = [
    { label: 'Đủ số tín chỉ', ok: graduation.creditsOk },
    { label: 'Giáo dục thể chất', ok: graduation.physicalEducationOk },
    { label: 'Giáo dục quốc phòng', ok: graduation.defenseEducationOk },
    { label: 'Chuẩn ngoại ngữ', ok: graduation.languageOk },
  ]
  const done = requirements.filter((r) => r.ok).length
  const rank = classifyGpa(graduation.gpa)

  return (
    <Card title="Tiến độ tốt nghiệp" description={`Đã đạt ${done}/${requirements.length} điều kiện`} icon={GraduationCap}>
      <div className="flex flex-col items-center gap-8 md:flex-row">
        <div className="flex flex-col items-center gap-2">
          <GpaRing gpa={graduation.gpa} />
          <Badge tone={rank.tone}>{rank.label}</Badge>
        </div>
        <ul className="grid w-full flex-1 gap-3 sm:grid-cols-2">
          {requirements.map(({ label, ok }) => (
            <li key={label} className={cn('flex items-center gap-3 rounded-xl border p-4', ok ? 'border-emerald-500/25 bg-emerald-500/5' : 'border-line bg-surface-2/50')}>
              {ok ? <CheckCircle2 className="shrink-0 text-emerald-500" size={20} /> : <CircleDashed className="shrink-0 text-muted" size={20} />}
              <span className={cn('text-sm font-medium', !ok && 'text-muted')}>{label}</span>
            </li>
          ))}
        </ul>
      </div>
    </Card>
  )
}

function SemesterCard({ semester }: { semester: SemesterSummary }) {
  const rank = classifyGpa(semester.gpa)
  return (
    <div className="rounded-2xl border border-line bg-surface p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-center justify-between">
        <p className="font-semibold">Học kỳ {semester.semester}</p>
        <Badge tone={rank.tone}>{rank.label}</Badge>
      </div>
      <p className="mt-4 text-4xl font-bold tracking-tight tabular-nums">{semester.gpa ?? '—'}</p>
      <p className="text-xs text-muted">Điểm TBC học kỳ</p>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-surface-2">
        <div className="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-500" style={{ width: `${((semester.gpa ?? 0) / 4) * 100}%` }} />
      </div>
      <div className="mt-4 flex justify-between text-sm text-muted">
        <span>{semester.credits ?? 0} tín chỉ</span>
        <span>{semester.courseCount} môn</span>
      </div>
    </div>
  )
}

export function AcademicSummaryPage() {
  return (
    <>
      <PageHeader title="Tổng kết & tốt nghiệp" description="Kết quả từng học kỳ và điều kiện xét tốt nghiệp" />
      <QueryState
        query={useAcademicSummary()}
        empty="Chưa có dữ liệu tổng kết học kỳ."
        emptyIcon={BarChart3}
        isEmpty={(data) => !data.semesters.length && !data.graduation}
      >
        {({ semesters, graduation }) => (
          <div className="space-y-6">
            {graduation && <GraduationPanel graduation={graduation} />}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {semesters.map((semester) => (
                <SemesterCard key={semester.semester} semester={semester} />
              ))}
            </div>
          </div>
        )}
      </QueryState>
    </>
  )
}
