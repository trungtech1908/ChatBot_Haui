import { ChevronRight } from 'lucide-react'
import { useMemo, useState } from 'react'

import { useCurriculum } from '@/api/students'
import { EmptyState } from '@/components/ui/EmptyState'
import { Figures } from '@/components/ui/Figures'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { SearchInput } from '@/components/ui/SearchInput'
import { Table, TBody, TD, TH, THead, TR } from '@/components/ui/Table'
import { cn } from '@/lib/cn'
import type { Curriculum, CurriculumGroup } from '@/types/student'

function GroupSection({ group, defaultOpen }: { group: CurriculumGroup; defaultOpen: boolean }) {
  const [open, setOpen] = useState(defaultOpen)
  const credits = group.courses.reduce((sum, c) => sum + c.credits, 0)

  return (
    <section className="rounded-md border border-line bg-surface">
      <button onClick={() => setOpen((v) => !v)} className="flex w-full items-center gap-2 px-4 py-2.5 text-left hover:bg-surface-2">
        <ChevronRight size={16} className={cn('shrink-0 text-muted transition-transform', open && 'rotate-90')} />
        <span className="min-w-0 flex-1 truncate text-sm font-semibold">{group.name}</span>
        <span className="hidden text-xs text-muted sm:inline">
          {group.type} · {group.courses.length} môn · {credits} TC{group.requiredCredits ? ` (yêu cầu ${group.requiredCredits})` : ''}
        </span>
      </button>
      {open && (
        <div className="border-t border-line">
          <Table>
            <THead>
              <tr>
                <TH className="w-28">Mã học phần</TH>
                <TH>Tên học phần</TH>
                <TH className="w-20 text-right">Số TC</TH>
                <TH className="w-24 text-right">Học kỳ</TH>
              </tr>
            </THead>
            <TBody>
              {group.courses.map((course) => (
                <TR key={course.code}>
                  <TD className="font-mono text-xs">{course.code}</TD>
                  <TD>{course.name}</TD>
                  <TD className="text-right tabular-nums">{course.credits}</TD>
                  <TD className="text-right tabular-nums">{course.semester}</TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </div>
      )}
    </section>
  )
}

function CurriculumView({ curriculum }: { curriculum: Curriculum }) {
  const [search, setSearch] = useState('')
  const courseCount = curriculum.groups.reduce((sum, g) => sum + g.courses.length, 0)

  const groups = useMemo(() => {
    const keyword = search.trim().toLowerCase()
    if (!keyword) return curriculum.groups
    return curriculum.groups
      .map((g) => ({ ...g, courses: g.courses.filter((c) => `${c.code} ${c.name}`.toLowerCase().includes(keyword)) }))
      .filter((g) => g.courses.length)
  }, [curriculum.groups, search])

  return (
    <>
      <PageHeader
        section="Học tập"
        title="Chương trình đào tạo"
        actions={<SearchInput value={search} onChange={setSearch} placeholder="Tìm mã hoặc tên học phần" />}
      />
      <Figures
        className="mb-5"
        items={[
          { label: 'Ngành', value: <span className="text-base">{curriculum.major}</span>, note: `Khóa ${curriculum.cohort}` },
          { label: 'Tín chỉ yêu cầu', value: curriculum.requiredCredits ?? '—' },
          { label: 'Khối kiến thức', value: curriculum.groups.length },
          { label: 'Tổng số học phần', value: courseCount },
        ]}
      />
      {groups.length ? (
        <div className="space-y-2">
          {groups.map((group, i) => (
            <GroupSection key={`${group.code}-${search}`} group={group} defaultOpen={i === 0 || !!search} />
          ))}
        </div>
      ) : (
        <EmptyState message="Không tìm thấy học phần phù hợp." />
      )}
    </>
  )
}

export function CurriculumPage() {
  return <QueryState query={useCurriculum()}>{(curriculum) => <CurriculumView curriculum={curriculum} />}</QueryState>
}
