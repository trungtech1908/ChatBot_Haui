import { AlertTriangle, CalendarClock, CalendarDays, CheckCircle2, Clock, Download, MapPin } from 'lucide-react'
import { useMemo, useState } from 'react'

import { useExams } from '@/api/students'
import { Alert } from '@/components/ui/Alert'
import { Badge } from '@/components/ui/Badge'
import { type Column, DataTable } from '@/components/ui/DataTable'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { SearchInput } from '@/components/ui/SearchInput'
import { Section } from '@/components/ui/Section'
import { Segmented } from '@/components/ui/Segmented'
import { Select } from '@/components/ui/Select'
import { StatGrid } from '@/components/ui/StatCard'
import { downloadCsv } from '@/lib/csv'
import { formatClock, formatDate, relativeDays, shortSemester } from '@/lib/format'
import type { ExamItem } from '@/types/student'

type When = 'all' | 'upcoming' | 'past'

const isUpcoming = (e: ExamItem) => !!e.startTime && new Date(e.startTime) >= new Date(new Date().toDateString())
const weekday = (value: string) => new Date(value).toLocaleDateString('vi-VN', { weekday: 'long' })

const columns: Column<ExamItem>[] = [
  {
    key: 'date', header: 'Ngày thi',
    render: (e) =>
      e.startTime ? (
        <div className="whitespace-nowrap">
          <p className="font-medium">{formatDate(e.startTime)}</p>
          <p className="text-xs text-muted first-letter:uppercase">{weekday(e.startTime)}</p>
        </div>
      ) : '—',
    sortValue: (e) => e.startTime,
  },
  { key: 'time', header: 'Giờ', render: (e) => <span className="tabular-nums">{formatClock(e.startTime)}{e.durationMinutes ? <span className="text-muted"> · {e.durationMinutes}′</span> : null}</span>, sortValue: (e) => e.startTime?.slice(11) },
  {
    key: 'course', header: 'Học phần',
    render: (e) => (
      <div className="min-w-48">
        <p className="font-medium">{e.courseName}</p>
        <p className="font-mono text-xs text-muted">{e.examCode}</p>
      </div>
    ),
    sortValue: (e) => e.courseName,
  },
  { key: 'room', header: 'Phòng', render: (e) => <span className="whitespace-nowrap">{e.room ?? '—'}</span>, sortValue: (e) => e.room },
  { key: 'seat', header: 'Vị trí', render: (e) => e.seat ?? '—' },
  { key: 'sbd', header: 'SBD', align: 'right', render: (e) => e.candidateNumber, sortValue: (e) => e.candidateNumber },
  { key: 'format', header: 'Hình thức', render: (e) => <span className="whitespace-nowrap">{e.format ?? '—'}</span>, sortValue: (e) => e.format },
  {
    key: 'eligible', header: 'Dự thi',
    render: (e) => (e.eligible ? <Badge tone="green">Đủ điều kiện</Badge> : <Badge tone="red" title={e.ineligibleReason ?? undefined}>Cấm thi</Badge>),
    sortValue: (e) => (e.eligible ? 1 : 0),
  },
  {
    key: 'countdown', header: '', align: 'right',
    render: (e) => (e.startTime && isUpcoming(e) ? <span className="text-xs font-medium whitespace-nowrap text-brand-ink">{relativeDays(e.startTime)}</span> : null),
  },
]

function NextExam({ exam }: { exam: ExamItem }) {
  return (
    <div className="card flex flex-col gap-4 p-5 sm:flex-row sm:items-center">
      <div className="flex h-16 w-16 shrink-0 flex-col items-center justify-center rounded-xl bg-brand-soft text-brand-ink">
        <span className="text-[11px] font-medium uppercase">Th{new Date(exam.startTime!).getMonth() + 1}</span>
        <span className="text-2xl leading-none font-semibold">{new Date(exam.startTime!).getDate()}</span>
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[13px] font-medium text-muted">Môn thi tiếp theo · <span className="text-brand-ink">{relativeDays(exam.startTime!)}</span></p>
        <p className="mt-0.5 text-lg font-semibold">{exam.courseName}</p>
        <div className="mt-1.5 flex flex-wrap gap-x-5 gap-y-1 text-[13px] text-fg-2">
          <span className="inline-flex items-center gap-1.5"><Clock size={14} className="text-muted" />{formatClock(exam.startTime)}{exam.durationMinutes ? ` · ${exam.durationMinutes} phút` : ''}</span>
          <span className="inline-flex items-center gap-1.5"><MapPin size={14} className="text-muted" />Phòng {exam.room ?? '—'}{exam.seat ? ` · vị trí ${exam.seat}` : ''}</span>
          <span>SBD <b className="font-semibold">{exam.candidateNumber}</b></span>
          {exam.format && <span>{exam.format}</span>}
        </div>
      </div>
      {!exam.eligible && <Badge variant="soft" tone="red">Cấm thi</Badge>}
    </div>
  )
}

function ExamsView({ exams }: { exams: ExamItem[] }) {
  const semesters = useMemo(() => {
    const seen = new Map<string, string>()
    exams.forEach((e) => seen.set(e.semesterCode, e.semester))
    return [...seen].sort((a, b) => b[0].localeCompare(a[0]))
  }, [exams])
  const [semester, setSemester] = useState(semesters[0][0])
  const [when, setWhen] = useState<When>('all')
  const [search, setSearch] = useState('')

  const current = exams.filter((e) => e.semesterCode === semester)
  const upcoming = current.filter(isUpcoming).sort((a, b) => a.startTime!.localeCompare(b.startTime!))
  const ineligible = current.filter((e) => !e.eligible)
  const keyword = search.trim().toLowerCase()
  const rows = current.filter((e) =>
    (when === 'all' || (when === 'upcoming') === isUpcoming(e))
    && (!keyword || `${e.courseName} ${e.examCode} ${e.room}`.toLowerCase().includes(keyword)))

  const exportCsv = () =>
    downloadCsv(
      `lich-thi-${semester}.csv`,
      ['Học phần', 'Lớp học phần', 'Ngày', 'Giờ', 'Thời lượng (phút)', 'Phòng', 'Vị trí', 'SBD', 'Hình thức', 'Đủ điều kiện'],
      rows.map((e) => [e.courseName, e.examCode, formatDate(e.startTime), formatClock(e.startTime), e.durationMinutes, e.room, e.seat, e.candidateNumber, e.format, e.eligible ? 'Có' : `Không (${e.ineligibleReason ?? ''})`]),
    )

  return (
    <>
      <PageHeader
        title="Lịch thi"
        description="Lịch thi kết thúc học phần"
        actions={
          <>
            <Select label="Học kỳ" value={semester} onChange={setSemester} options={semesters.map(([code, name]) => ({ value: code, label: shortSemester(name) }))} className="w-44" />
            <button onClick={exportCsv} className="btn-secondary"><Download size={15} />Xuất CSV</button>
          </>
        }
      />
      <div className="space-y-6">
        {ineligible.length > 0 && (
          <Alert tone="danger" title={`Bị cấm thi ${ineligible.length} học phần`}>
            {ineligible.map((e) => `${e.courseName}${e.ineligibleReason ? ` (${e.ineligibleReason})` : ''}`).join('; ')}
          </Alert>
        )}

        <StatGrid
          items={[
            { label: 'Số môn thi', value: current.length, note: shortSemester(semesters.find(([c]) => c === semester)?.[1]), icon: CalendarDays },
            { label: 'Sắp thi', value: upcoming.length, note: upcoming[0]?.startTime ? `Gần nhất ${relativeDays(upcoming[0].startTime)}` : 'Không còn môn nào', icon: CalendarClock },
            { label: 'Đã thi', value: current.length - upcoming.length, icon: CheckCircle2 },
            { label: 'Cấm thi', value: ineligible.length, note: ineligible.length ? 'Xem lý do ở bảng dưới' : 'Đủ điều kiện dự thi tất cả', icon: AlertTriangle, alert: ineligible.length > 0 },
          ]}
        />

        {upcoming[0] && <NextExam exam={upcoming[0]} />}

        <Section
          title="Danh sách môn thi"
          description={`${rows.length} môn`}
          toolbar={
            <>
              <Segmented<When>
                value={when}
                onChange={setWhen}
                options={[
                  { value: 'all', label: 'Tất cả', count: current.length },
                  { value: 'upcoming', label: 'Sắp thi', count: upcoming.length },
                  { value: 'past', label: 'Đã thi', count: current.length - upcoming.length },
                ]}
              />
              <SearchInput value={search} onChange={setSearch} placeholder="Tìm học phần, phòng…" className="sm:ml-auto" />
            </>
          }
          flush
        >
          <DataTable
            rows={rows}
            columns={columns}
            rowKey={(e) => `${e.examCode}-${e.startTime}-${e.candidateNumber}`}
            defaultSort={{ key: 'date', dir: 'asc' }}
            rowClassName={(e) => (!isUpcoming(e) ? 'text-fg-2' : undefined)}
          />
        </Section>
      </div>
    </>
  )
}

export function ExamsPage() {
  return (
    <QueryState query={useExams()} empty="Chưa có lịch thi.">
      {(exams) => <ExamsView exams={exams} />}
    </QueryState>
  )
}
