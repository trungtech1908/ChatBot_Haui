import { useState } from 'react'

import { useGrades } from '@/api/students'
import { EmptyState } from '@/components/ui/EmptyState'
import { Figures } from '@/components/ui/Figures'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { SearchInput } from '@/components/ui/SearchInput'
import { Table, TBody, TD, TH, THead, TR } from '@/components/ui/Table'
import { cn } from '@/lib/cn'
import type { Grade } from '@/types/student'

const score = (value: number | null) => (value == null ? '—' : value.toFixed(1))
const failed = (g: Grade) => g.letter?.startsWith('F')

function GradesView({ grades }: { grades: Grade[] }) {
  const [search, setSearch] = useState('')
  const keyword = search.trim().toLowerCase()
  const rows = keyword ? grades.filter((g) => `${g.courseCode} ${g.courseName}`.toLowerCase().includes(keyword)) : grades

  const totals = grades.map((g) => g.total).filter((v): v is number => v != null)
  const average = totals.length ? totals.reduce((a, b) => a + b, 0) / totals.length : null
  const failedCount = grades.filter(failed).length

  return (
    <>
      <PageHeader
        section="Học tập"
        title="Kết quả học tập"
        actions={<SearchInput value={search} onChange={setSearch} placeholder="Tìm học phần" />}
      />
      <Figures
        className="mb-5"
        items={[
          { label: 'Học phần đã có điểm', value: grades.length },
          { label: 'Điểm tổng kết trung bình (hệ 10)', value: score(average) },
          { label: 'Học phần không đạt', value: failedCount, alert: failedCount > 0 },
        ]}
      />

      {rows.length ? (
        <div className="rounded-md border border-line bg-surface">
          <Table>
            <THead>
              <tr>
                <TH className="w-28">Mã HP</TH>
                <TH>Tên học phần</TH>
                <TH className="text-right">TX1</TH>
                <TH className="text-right">TX2</TH>
                <TH className="text-right">Giữa kỳ</TH>
                <TH className="text-right">Cuối kỳ</TH>
                <TH className="text-right">Tổng kết</TH>
                <TH className="text-center">Điểm chữ</TH>
              </tr>
            </THead>
            <TBody>
              {rows.map((g, i) => (
                <TR key={`${g.courseCode}-${i}`}>
                  <TD className="font-mono text-xs">{g.courseCode}</TD>
                  <TD className="min-w-48">{g.courseName}</TD>
                  <TD className="text-right tabular-nums">{score(g.tx1)}</TD>
                  <TD className="text-right tabular-nums">{score(g.tx2)}</TD>
                  <TD className="text-right tabular-nums">{score(g.midterm)}</TD>
                  <TD className="text-right tabular-nums">{score(g.final)}</TD>
                  <TD className="text-right font-semibold tabular-nums">{score(g.total)}</TD>
                  <TD className={cn('text-center font-semibold', failed(g) && 'text-accent')}>{g.letter ?? '—'}</TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </div>
      ) : (
        <EmptyState message="Không tìm thấy học phần phù hợp." />
      )}
      <p className="mt-2 text-xs text-muted">Điểm chữ F: học phần chưa đạt, cần đăng ký học lại.</p>
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
