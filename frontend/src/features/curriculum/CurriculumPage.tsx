import { BookOpen, ChevronDown, Layers, Library, SearchX } from 'lucide-react'
import { useMemo, useState } from 'react'

import { useCurriculum } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { SearchInput } from '@/components/ui/SearchInput'
import { StatCard } from '@/components/ui/StatCard'
import { Table, TBody, TD, TH, THead, TR } from '@/components/ui/Table'
import { cn } from '@/lib/cn'
import type { Curriculum, CurriculumGroup } from '@/types/student'

function GroupSection({ group, defaultOpen }: { group: CurriculumGroup; defaultOpen: boolean }) {
  const [open, setOpen] = useState(defaultOpen)
  const credits = group.courses.reduce((sum, c) => sum + c.credits, 0)
  const required = group.type === 'Bắt buộc'

  return (
    <section className="overflow-hidden rounded-2xl border border-line bg-surface shadow-sm">
      <button onClick={() => setOpen((v) => !v)} className="flex w-full items-center gap-4 px-5 py-4 text-left transition hover:bg-surface-2/60">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary-soft text-primary">
          <Layers size={18} />
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold">{group.name}</p>
          <p className="text-sm text-muted">
            {group.courses.length} môn · {credits} tín chỉ{group.requiredCredits ? ` · yêu cầu ${group.requiredCredits} TC` : ''}
          </p>
        </div>
        <Badge tone={required ? 'red' : 'green'} className="hidden sm:inline-flex">{required ? 'Bắt buộc' : 'Tự chọn'}</Badge>
        <ChevronDown size={18} className={cn('shrink-0 text-muted transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <div className="border-t border-line">
          <Table>
            <THead>
              <tr>
                <TH className="w-32">Mã môn</TH>
                <TH>Tên môn học</TH>
                <TH className="w-24 text-center">Tín chỉ</TH>
                <TH className="w-24 text-center">Kỳ</TH>
              </tr>
            </THead>
            <TBody>
              {group.courses.map((course) => (
                <TR key={course.code}>
                  <TD className="font-mono text-xs font-semibold text-primary">{course.code}</TD>
                  <TD className="font-medium">{course.name}</TD>
                  <TD className="text-center tabular-nums">{course.credits}</TD>
                  <TD className="text-center">
                    <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-surface-2 text-xs font-semibold">{course.semester}</span>
                  </TD>
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
        title="Chương trình đào tạo"
        description={`${curriculum.major} · Khóa ${curriculum.cohort}`}
        actions={<SearchInput value={search} onChange={setSearch} placeholder="Tìm mã hoặc tên môn..." />}
      />
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <StatCard label="Tín chỉ yêu cầu" value={curriculum.requiredCredits ?? '---'} icon={BookOpen} tone="blue" />
        <StatCard label="Nhóm môn học" value={curriculum.groups.length} icon={Layers} tone="purple" />
        <StatCard label="Tổng số môn" value={courseCount} icon={Library} tone="green" />
      </div>
      {groups.length ? (
        <div className="space-y-3">
          {groups.map((group, i) => (
            <GroupSection key={`${group.code}-${search}`} group={group} defaultOpen={i === 0 || !!search} />
          ))}
        </div>
      ) : (
        <EmptyState message="Không tìm thấy môn học phù hợp." icon={SearchX} />
      )}
    </>
  )
}

export function CurriculumPage() {
  return <QueryState query={useCurriculum()}>{(curriculum) => <CurriculumView curriculum={curriculum} />}</QueryState>
}
