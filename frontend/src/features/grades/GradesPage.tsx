import { useState } from 'react'

import { useGrades } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { Figures } from '@/components/ui/Figures'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { SearchInput } from '@/components/ui/SearchInput'
import { Section } from '@/components/ui/Section'
import { Table, TBody, TD, TH, THead, TR } from '@/components/ui/Table'
import { letterTone } from '@/lib/format'
import type { Grade } from '@/types/student'

const score = (value: number | null) => (value == null ? '—' : value.toFixed(1))

function GradesView({ grades }: { grades: Grade[] }) {
  const [search, setSearch] = useState('')
  const keyword = search.trim().toLowerCase()
  const rows = keyword ? grades.filter((g) => `${g.courseCode} ${g.courseName}`.toLowerCase().includes(keyword)) : grades

  // Mỗi học phần chỉ tính lần học chính thức (điểm cao nhất), học lại không bị đếm trùng
  const official = grades.filter((g) => g.official)
  const totals = official.map((g) => g.total).filter((v): v is number => v != null)
  const average = totals.length ? totals.reduce((a, b) => a + b, 0) / totals.length : null
  const failedCount = official.filter((g) => g.letter?.startsWith('F')).length

  return (
    <>
      <PageHeader title="Kết quả học tập" description="Điểm quá trình, điểm thi và điểm học phần theo từng lần học" actions={<SearchInput value={search} onChange={setSearch} placeholder="Tìm học phần…" />} />
      <Figures
        className="mb-4 lg:grid-cols-3"
        items={[
          { label: 'Học phần có điểm', value: official.length },
          { label: 'Điểm tổng kết trung bình', value: score(average), note: 'Thang điểm 10' },
          { label: 'Học phần chưa đạt', value: failedCount, alert: failedCount > 0 },
        ]}
      />

      {rows.length ? (
        <Section flush>
          <Table>
            <THead>
              <tr>
                <TH>Học kỳ</TH>
                <TH>Học phần</TH>
                <TH className="text-right">Tín chỉ</TH>
                <TH className="text-right">Quá trình</TH>
                <TH className="text-right">Thi</TH>
                <TH className="text-right">Tổng kết</TH>
                <TH className="text-right">Điểm chữ</TH>
              </tr>
            </THead>
            <TBody>
              {rows.map((g, i) => (
                <TR key={`${g.courseCode}-${g.attempt}-${i}`}>
                  <TD className="whitespace-nowrap text-[13px] text-muted">{g.semester}</TD>
                  <TD className="min-w-56 py-2.5">
                    <p className="font-medium">{g.courseName}</p>
                    <p className="font-mono text-xs text-muted">
                      {g.courseCode}
                      {g.attempt > 1 && <span className="ml-2 font-sans">· học lần {g.attempt}</span>}
                    </p>
                  </TD>
                  <TD className="text-right tabular-nums">{g.credits}</TD>
                  <TD className="text-right text-muted tabular-nums">{score(g.process)}</TD>
                  <TD className="text-right tabular-nums">{score(g.exam)}</TD>
                  <TD className="text-right font-semibold tabular-nums">{score(g.total)}</TD>
                  <TD className="text-right">
                    <Badge tone={letterTone(g.letter)}>{g.letter ?? '—'}</Badge>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </Section>
      ) : (
        <EmptyState message="Không tìm thấy học phần phù hợp." />
      )}
    </>
  )
}

export function GradesPage() {
  return (
    <QueryState query={useGrades()} empty="Chưa có dữ liệu điểm học phần.">
      {(grades) => <GradesView grades={grades} />}
    </QueryState>
  )
}
