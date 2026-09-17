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

  const totals = grades.map((g) => g.total).filter((v): v is number => v != null)
  const average = totals.length ? totals.reduce((a, b) => a + b, 0) / totals.length : null
  const failedCount = grades.filter((g) => g.letter?.startsWith('F')).length

  return (
    <>
      <PageHeader title="Kết quả học tập" description="Điểm thành phần và điểm tổng kết học phần" actions={<SearchInput value={search} onChange={setSearch} placeholder="Tìm học phần…" />} />
      <Figures
        className="mb-4 lg:grid-cols-3"
        items={[
          { label: 'Học phần có điểm', value: grades.length },
          { label: 'Điểm tổng kết trung bình', value: score(average), note: 'Thang điểm 10' },
          { label: 'Học phần chưa đạt', value: failedCount, alert: failedCount > 0 },
        ]}
      />

      {rows.length ? (
        <Section flush>
          <Table>
            <THead>
              <tr>
                <TH>Học phần</TH>
                <TH className="text-right">TX1</TH>
                <TH className="text-right">TX2</TH>
                <TH className="text-right">Giữa kỳ</TH>
                <TH className="text-right">Cuối kỳ</TH>
                <TH className="text-right">Tổng kết</TH>
                <TH className="text-right">Điểm chữ</TH>
              </tr>
            </THead>
            <TBody>
              {rows.map((g, i) => (
                <TR key={`${g.courseCode}-${i}`}>
                  <TD className="min-w-56 py-2.5">
                    <p className="font-medium">{g.courseName}</p>
                    <p className="font-mono text-xs text-muted">{g.courseCode}</p>
                  </TD>
                  <TD className="text-right text-muted tabular-nums">{score(g.tx1)}</TD>
                  <TD className="text-right text-muted tabular-nums">{score(g.tx2)}</TD>
                  <TD className="text-right text-muted tabular-nums">{score(g.midterm)}</TD>
                  <TD className="text-right tabular-nums">{score(g.final)}</TD>
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
