import { Award, BookCheck, SearchX, Sigma } from 'lucide-react'
import { useState } from 'react'

import { useGrades } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { SearchInput } from '@/components/ui/SearchInput'
import { StatCard } from '@/components/ui/StatCard'
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
  const passed = grades.filter((g) => g.letter && !g.letter.startsWith('F')).length

  return (
    <>
      <PageHeader
        title="Kết quả học tập"
        description="Điểm thành phần và điểm tổng kết từng môn"
        actions={<SearchInput value={search} onChange={setSearch} placeholder="Tìm môn học..." />}
      />
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <StatCard label="Số môn đã học" value={grades.length} icon={BookCheck} tone="blue" />
        <StatCard label="Điểm tổng kết TB" value={score(average)} icon={Sigma} tone="purple" hint="Trung bình cộng các môn" />
        <StatCard label="Môn đạt" value={`${passed}/${grades.length}`} icon={Award} tone="green" />
      </div>

      {rows.length ? (
        <Card>
          <Table>
            <THead>
              <tr>
                <TH>Môn học</TH>
                <TH className="text-center">TX1</TH>
                <TH className="text-center">TX2</TH>
                <TH className="text-center">Giữa kỳ</TH>
                <TH className="text-center">Cuối kỳ</TH>
                <TH className="text-center">Tổng kết</TH>
                <TH className="text-center">Điểm chữ</TH>
              </tr>
            </THead>
            <TBody>
              {rows.map((g, i) => (
                <TR key={`${g.courseCode}-${i}`}>
                  <TD className="min-w-56">
                    <p className="font-medium">{g.courseName}</p>
                    <p className="font-mono text-xs text-muted">{g.courseCode}</p>
                  </TD>
                  <TD className="text-center text-muted tabular-nums">{score(g.tx1)}</TD>
                  <TD className="text-center text-muted tabular-nums">{score(g.tx2)}</TD>
                  <TD className="text-center text-muted tabular-nums">{score(g.midterm)}</TD>
                  <TD className="text-center tabular-nums">{score(g.final)}</TD>
                  <TD className="text-center font-bold tabular-nums">{score(g.total)}</TD>
                  <TD className="text-center">
                    <Badge tone={letterTone(g.letter)} className="min-w-9 justify-center">{g.letter ?? '—'}</Badge>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </Card>
      ) : (
        <EmptyState message="Không tìm thấy môn học phù hợp." icon={SearchX} />
      )}
    </>
  )
}

export function GradesPage() {
  return (
    <QueryState query={useGrades()} empty="Chưa có dữ liệu điểm môn học nào.">
      {(grades) => <GradesView grades={grades} />}
    </QueryState>
  )
}
