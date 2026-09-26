import { AlertCircle, CheckCircle2, Download, Layers, TrendingUp, XCircle } from 'lucide-react'
import { useMemo, useState } from 'react'

import { useAcademicSummary, useCurriculum, useGrades } from '@/api/students'
import { ColumnChart } from '@/components/charts/ColumnChart'
import { Badge } from '@/components/ui/Badge'
import { type Column, DataTable } from '@/components/ui/DataTable'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { SearchInput } from '@/components/ui/SearchInput'
import { Section } from '@/components/ui/Section'
import { Segmented } from '@/components/ui/Segmented'
import { Select } from '@/components/ui/Select'
import { StatGrid } from '@/components/ui/StatCard'
import { cn } from '@/lib/cn'
import { downloadCsv } from '@/lib/csv'
import { classification, classifyGpa, letterTone, REGISTRATION, score, shortSemester } from '@/lib/format'
import type { AcademicSummary, Grade, SemesterSummary } from '@/types/student'

type Status = 'all' | 'passed' | 'failed' | 'pending'
type Attempt = 'all' | 'lan_dau' | 'hoc_lai' | 'cai_thien'
type View = 'semester' | 'list'

const LETTERS = ['A', 'B+', 'B', 'C+', 'C', 'D+', 'D', 'F']

const statusOf = (g: Grade): Exclude<Status, 'all'> => (g.passed == null ? 'pending' : g.passed ? 'passed' : 'failed')

function CourseCell({ g }: { g: Grade }) {
  return (
    <div className="min-w-56 py-1">
      <p className={cn('font-medium', !g.official && 'text-muted')}>{g.courseName}</p>
      <div className="mt-0.5 flex flex-wrap items-center gap-1.5 text-xs text-muted">
        <span className="font-mono">{g.courseCode}</span>
        {g.registration && g.registration !== 'lan_dau' && <Badge variant="soft" tone="purple">{REGISTRATION[g.registration]}</Badge>}
        {!g.countsGpa && <Badge variant="soft">Không tính TB</Badge>}
        {!g.official && g.passed != null && <span title="Không phải lần học được dùng tính điểm tích lũy">· lần {g.attempt}, không tính tích lũy</span>}
      </div>
    </div>
  )
}

function columns(withSemester: boolean): Column<Grade>[] {
  return [
    ...(withSemester
      ? [{ key: 'semester', header: 'Học kỳ', render: (g: Grade) => <span className="whitespace-nowrap text-fg-2">{shortSemester(g.semester)}</span>, sortValue: (g: Grade) => g.semesterCode }]
      : []),
    { key: 'course', header: 'Học phần', render: (g) => <CourseCell g={g} />, sortValue: (g) => g.courseName },
    { key: 'credits', header: 'TC', align: 'right', render: (g) => g.credits, sortValue: (g) => g.credits },
    { key: 'process', header: 'Quá trình', align: 'right', render: (g) => <span className="text-fg-2">{score(g.process)}</span>, sortValue: (g) => g.process },
    { key: 'exam', header: 'Thi', align: 'right', render: (g) => <span className="text-fg-2">{score(g.exam)}</span>, sortValue: (g) => g.exam },
    { key: 'total', header: 'Hệ 10', align: 'right', render: (g) => <span className="font-semibold">{score(g.total)}</span>, sortValue: (g) => g.total },
    { key: 'grade4', header: 'Hệ 4', align: 'right', render: (g) => score(g.grade4), sortValue: (g) => g.grade4 },
    {
      key: 'letter', header: 'Điểm chữ', align: 'center',
      render: (g) => (g.letter ? <Badge variant="soft" tone={letterTone(g.letter)} className="min-w-8 justify-center">{g.letter}</Badge> : '—'),
      sortValue: (g) => g.grade4 ?? (g.passed ? 0.5 : g.passed === false ? -1 : null),
    },
  ]
}

function SemesterHeader({ name, summary }: { name: string; summary?: SemesterSummary }) {
  const rank = classification(summary?.classification)
  const conduct = classification(summary?.conductClassification)
  return (
    <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2 border-y border-line bg-surface-2 px-5 py-2.5">
      <p className="font-semibold">{name}</p>
      {summary ? (
        <dl className="flex flex-wrap items-center gap-x-5 gap-y-1 text-[13px]">
          <div className="flex gap-1.5"><dt className="text-muted">TB kỳ</dt><dd className="font-semibold tabular-nums">{score(summary.gpa, 2)}</dd></div>
          <div className="flex gap-1.5"><dt className="text-muted">TC đạt</dt><dd className="font-medium tabular-nums">{summary.credits}/{summary.creditsRegistered}</dd></div>
          <div className="flex items-center gap-1.5"><dt className="text-muted">Học lực</dt><dd><Badge tone={rank.tone}>{rank.label}</Badge></dd></div>
          <div className="flex items-center gap-1.5"><dt className="text-muted">Rèn luyện</dt><dd><Badge tone={conduct.tone}>{summary.conductScore ?? '—'} · {conduct.label}</Badge></dd></div>
          {summary.warning && <Badge variant="soft" tone="red">Cảnh báo học tập</Badge>}
        </dl>
      ) : (
        <p className="text-[13px] text-muted">Học kỳ phụ — kết quả gộp vào học kỳ chính liền trước</p>
      )}
    </div>
  )
}

function GradesView({ grades, summary, requiredCredits }: { grades: Grade[]; summary?: AcademicSummary; requiredCredits?: number | null }) {
  const [semester, setSemester] = useState('all')
  const [status, setStatus] = useState<Status>('all')
  const [attempt, setAttempt] = useState<Attempt>('all')
  const [officialOnly, setOfficialOnly] = useState(false)
  const [search, setSearch] = useState('')
  const [view, setView] = useState<View>('semester')

  const semesters = useMemo(() => {
    const seen = new Map<string, string>()
    grades.forEach((g) => seen.set(g.semesterCode, g.semester))
    return [...seen].sort((a, b) => b[0].localeCompare(a[0]))
  }, [grades])
  const summaryByCode = useMemo(() => new Map(summary?.semesters.map((s) => [s.code, s]) ?? []), [summary])

  // Lọc theo mọi điều kiện trừ trạng thái — để đếm số lượng trên các chip trạng thái
  const base = useMemo(() => {
    const keyword = search.trim().toLowerCase()
    return grades.filter((g) =>
      (semester === 'all' || g.semesterCode === semester)
      && (attempt === 'all' || g.registration === attempt)
      && (!officialOnly || g.official)
      && (!keyword || `${g.courseCode} ${g.courseName}`.toLowerCase().includes(keyword)))
  }, [grades, semester, attempt, officialOnly, search])
  const rows = status === 'all' ? base : base.filter((g) => statusOf(g) === status)
  const count = (s: Exclude<Status, 'all'>) => base.filter((g) => statusOf(g) === s).length

  const official = grades.filter((g) => g.official)
  const failed = official.filter((g) => g.passed === false)
  const pending = official.filter((g) => g.passed == null)
  const graduation = summary?.graduation
  const trend = summary?.semesters.map((s) => s.cumulativeGpa) ?? []

  // Phân bố điểm chữ: lần học chính thức, học phần tính TB, trong phạm vi đang lọc học kỳ
  const distributionSource = (semester === 'all' ? official : grades.filter((g) => g.semesterCode === semester && g.official)).filter((g) => g.countsGpa && g.letter)
  const distribution = LETTERS.map((l) => distributionSource.filter((g) => g.letter === l).length)
  const totalGraded = distribution.reduce((a, b) => a + b, 0)

  const exportCsv = () =>
    downloadCsv(
      'bang-diem.csv',
      ['Học kỳ', 'Mã học phần', 'Tên học phần', 'Tín chỉ', 'Lần học', 'Quá trình', 'Thi', 'Hệ 10', 'Hệ 4', 'Điểm chữ', 'Chính thức'],
      rows.map((g) => [g.semester, g.courseCode, g.courseName, g.credits, g.attempt, g.process, g.exam, g.total, g.grade4, g.letter, g.official ? 'Có' : 'Không']),
    )

  const toolbar = (
    <>
      <Select
        label="Học kỳ"
        value={semester}
        onChange={setSemester}
        options={[{ value: 'all', label: 'Tất cả học kỳ' }, ...semesters.map(([code, name]) => ({ value: code, label: shortSemester(name) }))]}
        className="w-44"
      />
      <Segmented<Status>
        value={status}
        onChange={setStatus}
        options={[
          { value: 'all', label: 'Tất cả', count: base.length },
          { value: 'passed', label: 'Đạt', count: count('passed') },
          { value: 'failed', label: 'Chưa đạt', count: count('failed') },
          { value: 'pending', label: 'Chưa có điểm', count: count('pending') },
        ]}
      />
      <Select<Attempt>
        label="Lần học"
        value={attempt}
        onChange={setAttempt}
        options={[
          { value: 'all', label: 'Mọi lần học' },
          { value: 'lan_dau', label: 'Học lần đầu' },
          { value: 'hoc_lai', label: 'Học lại' },
          { value: 'cai_thien', label: 'Học cải thiện' },
        ]}
        className="w-40"
      />
      <label className="inline-flex h-9 cursor-pointer items-center gap-2 rounded-lg px-1 text-[13px] text-fg-2 select-none">
        <input type="checkbox" checked={officialOnly} onChange={(e) => setOfficialOnly(e.target.checked)} className="h-4 w-4 accent-[var(--brand)]" />
        Chỉ lần học tính tích lũy
      </label>
      <SearchInput value={search} onChange={setSearch} placeholder="Tìm mã hoặc tên học phần…" className="sm:ml-auto" />
    </>
  )

  const groups = semesters.filter(([code]) => rows.some((g) => g.semesterCode === code))

  return (
    <>
      <PageHeader
        title="Kết quả học tập"
        description={`${official.length} học phần · ${semesters.length} học kỳ`}
        actions={<button onClick={exportCsv} className="btn-secondary"><Download size={15} />Xuất CSV</button>}
      />

      <div className="space-y-6">
        <StatGrid
          items={[
            { label: 'GPA tích lũy', value: score(graduation?.gpa, 2), note: `Thang 4 · ${classifyGpa(graduation?.gpa ?? null).label}`, icon: TrendingUp, trend },
            { label: 'Tín chỉ tích lũy', value: graduation ? `${graduation.credits}${requiredCredits ? ` / ${requiredCredits}` : ''}` : '—', note: requiredCredits && graduation ? `${Math.round((graduation.credits / requiredCredits) * 100)}% chương trình` : undefined, icon: Layers },
            { label: 'Học phần đã đạt', value: official.filter((g) => g.passed).length, note: `trên ${official.length} học phần đã học`, icon: CheckCircle2 },
            { label: 'Học phần chưa đạt', value: failed.length, note: pending.length ? `${pending.length} học phần chưa có điểm` : 'Tính theo lần học chính thức', icon: XCircle, alert: failed.length > 0 },
          ]}
        />

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
          <Section
            title="Bảng điểm"
            description={`${rows.length} dòng`}
            aside={
              <Segmented<View>
                value={view}
                onChange={setView}
                options={[{ value: 'semester', label: 'Theo học kỳ' }, { value: 'list', label: 'Danh sách' }]}
              />
            }
            toolbar={toolbar}
            flush
          >
            {view === 'list' || !rows.length ? (
              <DataTable rows={rows} columns={columns(true)} rowKey={(g) => `${g.semesterCode}-${g.courseCode}-${g.attempt}`} defaultSort={{ key: 'semester', dir: 'desc' }} />
            ) : (
              groups.map(([code, name]) => (
                <div key={code} className="first:[&>div:first-child]:border-t-0">
                  <SemesterHeader name={name} summary={summaryByCode.get(code)} />
                  <DataTable rows={rows.filter((g) => g.semesterCode === code)} columns={columns(false)} rowKey={(g) => `${g.courseCode}-${g.attempt}`} />
                </div>
              ))
            )}
          </Section>

          <div className="space-y-6">
            <Section title="Phân bố điểm chữ" description={`${totalGraded} học phần tính điểm trung bình${semester === 'all' ? '' : ` · ${shortSemester(semesters.find(([c]) => c === semester)?.[1])}`}`}>
              {totalGraded ? (
                <ColumnChart
                  categories={LETTERS}
                  values={distribution}
                  label={`Phân bố điểm chữ: ${LETTERS.map((l, i) => `${l} ${distribution[i]}`).join(', ')}`}
                  tooltip={(i) => `${LETTERS[i]}: ${distribution[i]} học phần (${Math.round((distribution[i] / totalGraded) * 100)}%)`}
                />
              ) : (
                <p className="py-8 text-center text-muted">Chưa có điểm.</p>
              )}
            </Section>

            <Section title="Cần chú ý" description="Học phần chưa đạt hoặc chưa có điểm" flush>
              {failed.length + pending.length ? (
                <ul className="divide-y divide-line">
                  {[...failed, ...pending].map((g) => (
                    <li key={`${g.courseCode}-${g.attempt}`} className="flex items-center gap-3 px-5 py-3">
                      <AlertCircle size={16} className={g.passed === false ? 'shrink-0 text-danger' : 'shrink-0 text-warning'} />
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-medium">{g.courseName}</p>
                        <p className="text-xs text-muted">{shortSemester(g.semester)} · {g.credits} TC</p>
                      </div>
                      <Badge variant="soft" tone={g.passed === false ? 'red' : 'yellow'}>{g.letter ?? 'Chưa có'}</Badge>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="flex items-center gap-2 px-5 py-6 text-success"><CheckCircle2 size={16} />Không có học phần nào cần chú ý.</p>
              )}
            </Section>
          </div>
        </div>
      </div>
    </>
  )
}

export function GradesPage() {
  const summary = useAcademicSummary().data
  const requiredCredits = useCurriculum().data?.requiredCredits
  return (
    <QueryState query={useGrades()} empty="Chưa có dữ liệu điểm học phần.">
      {(grades) => <GradesView grades={grades} summary={summary} requiredCredits={requiredCredits} />}
    </QueryState>
  )
}
