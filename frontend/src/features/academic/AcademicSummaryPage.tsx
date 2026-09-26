import { Award, Check, Layers, Minus, ShieldCheck, TrendingUp } from 'lucide-react'
import { useState } from 'react'

import { useAcademicSummary, useCurriculum } from '@/api/students'
import { ColumnChart } from '@/components/charts/ColumnChart'
import { LineChart } from '@/components/charts/LineChart'
import { Alert } from '@/components/ui/Alert'
import { Badge } from '@/components/ui/Badge'
import { type Column, DataTable } from '@/components/ui/DataTable'
import { PageHeader } from '@/components/ui/PageHeader'
import { Progress } from '@/components/ui/Progress'
import { QueryState } from '@/components/ui/QueryState'
import { Section } from '@/components/ui/Section'
import { Segmented } from '@/components/ui/Segmented'
import { StatGrid } from '@/components/ui/StatCard'
import { cn } from '@/lib/cn'
import { classification, classifyGpa, score, shortSemester } from '@/lib/format'
import type { SemesterSummary } from '@/types/student'

type Metric = 'gpa' | 'conduct'

const columns: Column<SemesterSummary>[] = [
  {
    key: 'semester', header: 'Học kỳ',
    render: (s) => (
      <span className="inline-flex items-center gap-2 font-medium whitespace-nowrap">
        {s.semester}
        {s.warning && <Badge variant="soft" tone="red">Cảnh báo</Badge>}
      </span>
    ),
    sortValue: (s) => s.code,
  },
  { key: 'courses', header: 'Học phần', align: 'right', render: (s) => s.courseCount, sortValue: (s) => s.courseCount },
  {
    key: 'credits', header: 'TC đạt / ĐK', align: 'right',
    render: (s) => (
      <span>
        {s.credits ?? '—'}<span className="text-muted"> / {s.creditsRegistered ?? '—'}</span>
        {!!s.creditsFailed && <span className="ml-1.5 text-danger">(−{s.creditsFailed})</span>}
      </span>
    ),
    sortValue: (s) => s.credits,
  },
  { key: 'gpa', header: 'TB kỳ', align: 'right', render: (s) => <span className="font-semibold">{score(s.gpa, 2)}</span>, sortValue: (s) => s.gpa },
  { key: 'cumulative', header: 'TB tích lũy', align: 'right', render: (s) => score(s.cumulativeGpa, 2), sortValue: (s) => s.cumulativeGpa },
  { key: 'cumulativeCredits', header: 'TC tích lũy', align: 'right', render: (s) => s.cumulativeCredits ?? '—', sortValue: (s) => s.cumulativeCredits },
  {
    key: 'rank', header: 'Học lực',
    render: (s) => { const c = classification(s.classification); return <Badge tone={c.tone}>{c.label}</Badge> },
    sortValue: (s) => s.gpa,
  },
  {
    key: 'conduct', header: 'Rèn luyện',
    render: (s) => { const c = classification(s.conductClassification); return s.conductScore == null ? '—' : <Badge tone={c.tone}>{s.conductScore} · {c.label}</Badge> },
    sortValue: (s) => s.conductScore,
  },
]

export function AcademicSummaryPage() {
  const requiredCredits = useCurriculum().data?.requiredCredits ?? 0
  const [metric, setMetric] = useState<Metric>('gpa')

  return (
    <>
      <PageHeader title="Tiến độ & tốt nghiệp" description="Kết quả theo học kỳ và điều kiện xét tốt nghiệp" />
      <QueryState query={useAcademicSummary()} empty="Chưa có dữ liệu tổng kết học kỳ." isEmpty={(data) => !data.semesters.length && !data.graduation}>
        {({ semesters, graduation }) => {
          const earned = graduation?.credits ?? 0
          const requirements = graduation
            ? ([
                ['Tích lũy đủ tín chỉ chương trình', graduation.creditsOk, requiredCredits ? `${earned}/${requiredCredits} tín chỉ` : undefined],
                ['Chứng chỉ Giáo dục thể chất', graduation.physicalEducationOk, undefined],
                ['Chứng chỉ Giáo dục quốc phòng – an ninh', graduation.defenseEducationOk, undefined],
                ['Chuẩn đầu ra ngoại ngữ', graduation.languageOk, undefined],
              ] as const)
            : []
          const done = requirements.filter(([, ok]) => ok).length
          // Học kỳ phụ không có tổng kết riêng → chỉ vẽ học kỳ có điểm TB
          const main = semesters.filter((s) => s.gpa != null || s.cumulativeGpa != null)
          const categories = main.map((s) => shortSemester(s.semester))
          const conducts = main.map((s) => s.conductScore ?? 0)
          const warnings = semesters.filter((s) => s.warning)
          const avgConduct = main.filter((s) => s.conductScore != null)
          const conductMean = avgConduct.length ? Math.round(avgConduct.reduce((a, s) => a + (s.conductScore ?? 0), 0) / avgConduct.length) : null
          const rank = classifyGpa(graduation?.gpa ?? null)

          return (
            <div className="space-y-6">
              {warnings.length > 0 && (
                <Alert tone="danger" title={`Bị cảnh báo học tập ${warnings.length} lần`}>
                  {warnings.map((w) => w.semester).join(', ')}
                </Alert>
              )}

              <StatGrid
                items={[
                  { label: 'GPA tích lũy', value: score(graduation?.gpa, 2), note: `Thang 4 · ${rank.label}`, icon: TrendingUp, trend: main.map((s) => s.cumulativeGpa) },
                  { label: 'Tín chỉ tích lũy', value: requiredCredits ? `${earned} / ${requiredCredits}` : earned, note: requiredCredits ? `Còn ${Math.max(0, requiredCredits - earned)} tín chỉ` : undefined, icon: Layers, trend: main.map((s) => s.cumulativeCredits) },
                  { label: 'Rèn luyện trung bình', value: conductMean ?? '—', note: `${avgConduct.length} học kỳ`, icon: Award, trend: main.map((s) => s.conductScore) },
                  { label: 'Điều kiện tốt nghiệp', value: `${done}/${requirements.length}`, note: done === requirements.length ? 'Đã đủ điều kiện' : `Còn ${requirements.length - done} điều kiện`, icon: ShieldCheck },
                ]}
              />

              <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
                <Section
                  title={metric === 'gpa' ? 'Điểm trung bình theo học kỳ' : 'Điểm rèn luyện theo học kỳ'}
                  description={metric === 'gpa' ? 'Thang điểm 4' : 'Thang điểm 100'}
                  aside={
                    <Segmented<Metric>
                      value={metric}
                      onChange={setMetric}
                      options={[{ value: 'gpa', label: 'Học tập' }, { value: 'conduct', label: 'Rèn luyện' }]}
                    />
                  }
                >
                  {main.length ? (
                    metric === 'gpa' ? (
                      <LineChart
                        categories={categories}
                        series={[
                          { name: 'TB học kỳ', color: 'var(--chart-1)', values: main.map((s) => s.gpa) },
                          { name: 'TB tích lũy', color: 'var(--chart-2)', values: main.map((s) => s.cumulativeGpa) },
                        ]}
                        domain={[0, 4]}
                        ticks={[0, 1, 2, 3, 4]}
                        height={260}
                        label={`Điểm trung bình học kỳ và tích lũy qua ${main.length} học kỳ`}
                      />
                    ) : (
                      <ColumnChart
                        categories={categories}
                        values={conducts}
                        max={100}
                        height={260}
                        label={`Điểm rèn luyện qua ${main.length} học kỳ`}
                        tooltip={(i) => `${main[i].semester}: ${main[i].conductScore ?? '—'} điểm · ${classification(main[i].conductClassification).label}`}
                      />
                    )
                  ) : (
                    <p className="py-10 text-center text-muted">Chưa có học kỳ nào được tổng kết.</p>
                  )}
                </Section>

                {graduation && (
                  <Section title="Điều kiện xét tốt nghiệp" description={done === requirements.length ? 'Đã đủ điều kiện xét tốt nghiệp' : `Đạt ${done}/${requirements.length} điều kiện`}>
                    {requiredCredits > 0 && (
                      <div className="mb-5">
                        <div className="mb-2 flex items-baseline justify-between text-[13px]">
                          <span className="text-muted">Tiến độ tín chỉ</span>
                          <span className="font-semibold tabular-nums">{Math.round((earned / requiredCredits) * 100)}%</span>
                        </div>
                        <Progress value={earned} max={requiredCredits} />
                      </div>
                    )}
                    <ul className="space-y-3">
                      {requirements.map(([label, ok, note]) => (
                        <li key={label} className="flex items-start gap-3">
                          <span className={cn('mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full', ok ? 'bg-success-soft text-success' : 'bg-hover text-muted')}>
                            {ok ? <Check size={12} strokeWidth={3} /> : <Minus size={12} strokeWidth={3} />}
                          </span>
                          <div>
                            <p className={ok ? 'font-medium' : 'text-fg-2'}>{label}</p>
                            <p className="text-xs text-muted">{ok ? 'Đã đạt' : 'Chưa đạt'}{note ? ` · ${note}` : ''}</p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </Section>
                )}
              </div>

              <Section title="Tổng kết theo học kỳ" description={`${semesters.length} học kỳ · bấm tiêu đề cột để sắp xếp`} flush>
                <DataTable rows={semesters} columns={columns} rowKey={(s) => s.code} defaultSort={{ key: 'semester', dir: 'desc' }} />
              </Section>
            </div>
          )
        }}
      </QueryState>
    </>
  )
}
