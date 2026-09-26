import { BookOpen, CheckCircle2, ChevronRight, Clock, XCircle } from 'lucide-react'
import { useMemo, useState } from 'react'

import { useCurriculum } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { type Column, DataTable } from '@/components/ui/DataTable'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageHeader } from '@/components/ui/PageHeader'
import { Progress } from '@/components/ui/Progress'
import { QueryState } from '@/components/ui/QueryState'
import { SearchInput } from '@/components/ui/SearchInput'
import { Segmented } from '@/components/ui/Segmented'
import { Select } from '@/components/ui/Select'
import { StatGrid } from '@/components/ui/StatCard'
import { cn } from '@/lib/cn'
import { letterTone, semesterFromCode } from '@/lib/format'
import type { CourseStatus, Curriculum, CurriculumCourse, CurriculumGroup } from '@/types/student'
import type { Tone } from '@/types/ui'

const STATUS: Record<CourseStatus, { label: string; tone: Tone }> = {
  da_dat: { label: 'Đã đạt', tone: 'green' },
  chua_dat: { label: 'Chưa đạt', tone: 'red' },
  chua_co_diem: { label: 'Đang học', tone: 'yellow' },
  chua_hoc: { label: 'Chưa học', tone: 'gray' },
}
const STATUS_ORDER: CourseStatus[] = ['chua_dat', 'chua_co_diem', 'chua_hoc', 'da_dat']

const columns: Column<CurriculumCourse>[] = [
  { key: 'code', header: 'Mã HP', render: (c) => <span className="font-mono text-xs text-muted">{c.code}</span>, sortValue: (c) => c.code, className: 'w-28' },
  { key: 'name', header: 'Tên học phần', render: (c) => <span className="font-medium">{c.name}</span>, sortValue: (c) => c.name },
  { key: 'credits', header: 'TC', align: 'right', render: (c) => c.credits, sortValue: (c) => c.credits },
  { key: 'plan', header: 'Kỳ kế hoạch', align: 'right', render: (c) => c.semester ?? '—', sortValue: (c) => c.semester },
  { key: 'taken', header: 'Đã học', render: (c) => <span className="whitespace-nowrap text-fg-2">{c.takenSemester ? semesterFromCode(c.takenSemester) : '—'}</span>, sortValue: (c) => c.takenSemester },
  { key: 'letter', header: 'Điểm', align: 'center', render: (c) => (c.letter ? <Badge variant="soft" tone={letterTone(c.letter)}>{c.letter}</Badge> : '—'), sortValue: (c) => c.letter },
  {
    key: 'status', header: 'Trạng thái',
    render: (c) => <Badge tone={STATUS[c.status].tone}>{STATUS[c.status].label}</Badge>,
    sortValue: (c) => STATUS_ORDER.indexOf(c.status),
  },
]

const earnedCredits = (courses: CurriculumCourse[]) => courses.filter((c) => c.status === 'da_dat').reduce((s, c) => s + c.credits, 0)

function GroupSection({ group, visible, defaultOpen }: { group: CurriculumGroup; visible: CurriculumCourse[]; defaultOpen: boolean }) {
  const [open, setOpen] = useState(defaultOpen)
  const earned = earnedCredits(group.courses)
  const target = group.requiredCredits ?? group.courses.reduce((s, c) => s + c.credits, 0)
  const complete = earned >= target

  return (
    <section className="card overflow-hidden">
      <button onClick={() => setOpen((v) => !v)} aria-expanded={open} className="flex w-full items-center gap-4 px-5 py-4 text-left transition-colors hover:bg-hover/60">
        <ChevronRight size={16} className={cn('shrink-0 text-muted transition-transform', open && 'rotate-90')} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold">{group.name}</span>
            <Badge variant="soft" tone={group.type === 'Bắt buộc' ? 'blue' : 'purple'}>{group.type}</Badge>
            {complete && <Badge variant="soft" tone="green">Hoàn thành</Badge>}
          </div>
          <p className="mt-0.5 text-[13px] text-muted">
            {group.courses.length} học phần{group.type === 'Tự chọn' ? ` · chọn đủ ${target} tín chỉ` : ''}
            {visible.length !== group.courses.length && ` · ${visible.length} khớp bộ lọc`}
          </p>
        </div>
        <div className="hidden w-44 shrink-0 sm:block">
          <div className="mb-1.5 flex justify-between text-xs">
            <span className="text-muted">Tín chỉ đạt</span>
            <span className="font-semibold tabular-nums">{Math.min(earned, target)}/{target}</span>
          </div>
          <Progress value={earned} max={target} tone={complete ? 'success' : 'brand'} />
        </div>
      </button>
      {open && (
        <div className="border-t border-line">
          <DataTable rows={visible} columns={columns} rowKey={(c) => c.code} defaultSort={{ key: 'plan', dir: 'asc' }} dense />
        </div>
      )}
    </section>
  )
}

function CurriculumView({ curriculum }: { curriculum: Curriculum }) {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<CourseStatus | 'all'>('all')
  const [plan, setPlan] = useState('all')

  const all = curriculum.groups.flatMap((g) => g.courses)
  const planSemesters = [...new Set(all.map((c) => c.semester).filter((s) => s != null))].sort((a, b) => a - b)
  const count = (s: CourseStatus) => all.filter((c) => c.status === s).length

  // Tín chỉ tích lũy theo CTĐT: bắt buộc đạt + tự chọn đạt (tối đa bằng yêu cầu của nhóm)
  const earned = curriculum.groups.reduce((sum, g) => {
    const e = earnedCredits(g.courses)
    return sum + (g.type === 'Tự chọn' && g.requiredCredits ? Math.min(e, g.requiredCredits) : e)
  }, 0)
  const required = curriculum.requiredCredits ?? curriculum.groups.reduce((s, g) => s + (g.requiredCredits ?? 0), 0)

  const filtered = useMemo(() => {
    const keyword = search.trim().toLowerCase()
    return curriculum.groups.map((g) => ({
      group: g,
      visible: g.courses.filter((c) =>
        (status === 'all' || c.status === status)
        && (plan === 'all' || String(c.semester) === plan)
        && (!keyword || `${c.code} ${c.name}`.toLowerCase().includes(keyword))),
    }))
  }, [curriculum.groups, search, status, plan])
  const shown = filtered.filter((g) => g.visible.length)
  const filtering = status !== 'all' || plan !== 'all' || !!search.trim()

  return (
    <>
      <PageHeader title="Chương trình đào tạo" description={`${curriculum.major} · Khóa ${curriculum.cohort}`} />
      <div className="space-y-6">
        <StatGrid
          items={[
            { label: 'Tín chỉ theo chương trình', value: `${earned} / ${required}`, note: `${required ? Math.round((earned / required) * 100) : 0}% hoàn thành`, icon: BookOpen },
            { label: 'Học phần đã đạt', value: count('da_dat'), note: `trên ${all.length} học phần trong chương trình`, icon: CheckCircle2 },
            { label: 'Đang học', value: count('chua_co_diem'), note: 'Chưa có điểm tổng kết', icon: Clock },
            { label: 'Chưa đạt', value: count('chua_dat'), note: 'Cần học lại', icon: XCircle, alert: count('chua_dat') > 0 },
          ]}
        />

        <div className="card flex flex-wrap items-center gap-2 p-3">
          <Segmented<CourseStatus | 'all'>
            value={status}
            onChange={setStatus}
            options={[
              { value: 'all', label: 'Tất cả', count: all.length },
              { value: 'da_dat', label: 'Đã đạt', count: count('da_dat') },
              { value: 'chua_co_diem', label: 'Đang học', count: count('chua_co_diem') },
              { value: 'chua_dat', label: 'Chưa đạt', count: count('chua_dat') },
              { value: 'chua_hoc', label: 'Chưa học', count: count('chua_hoc') },
            ]}
          />
          <Select
            label="Học kỳ kế hoạch"
            value={plan}
            onChange={setPlan}
            options={[{ value: 'all', label: 'Mọi kỳ kế hoạch' }, ...planSemesters.map((s) => ({ value: String(s), label: `Kỳ ${s}` }))]}
            className="w-44"
          />
          {filtering && (
            <button onClick={() => { setStatus('all'); setPlan('all'); setSearch('') }} className="btn-ghost h-9">Xóa lọc</button>
          )}
          <SearchInput value={search} onChange={setSearch} placeholder="Tìm mã hoặc tên học phần…" className="sm:ml-auto" />
        </div>

        {shown.length ? (
          <div className="space-y-3">
            {shown.map(({ group, visible }, i) => (
              <GroupSection key={`${group.code}-${filtering}`} group={group} visible={visible} defaultOpen={i === 0 || filtering} />
            ))}
          </div>
        ) : (
          <EmptyState message="Không có học phần nào khớp bộ lọc." />
        )}
      </div>
    </>
  )
}

export function CurriculumPage() {
  return <QueryState query={useCurriculum()}>{(curriculum) => <CurriculumView curriculum={curriculum} />}</QueryState>
}
