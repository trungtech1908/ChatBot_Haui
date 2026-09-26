import { CalendarDays, Clock, MapPin, User } from 'lucide-react'
import { useMemo, useState } from 'react'

import { useSchedule } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { type Column, DataTable } from '@/components/ui/DataTable'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { SearchInput } from '@/components/ui/SearchInput'
import { Section } from '@/components/ui/Section'
import { Segmented } from '@/components/ui/Segmented'
import { Select } from '@/components/ui/Select'
import { cn } from '@/lib/cn'
import { shortSemester, todayWeekday, weekdayLabel } from '@/lib/format'
import type { ScheduleItem } from '@/types/student'

const WEEKDAYS = [2, 3, 4, 5, 6, 7, 8]
const SHORT_DAY: Record<number, string> = { 2: 'T2', 3: 'T3', 4: 'T4', 5: 'T5', 6: 'T6', 7: 'T7', 8: 'CN' }
const ROW_H = 30 // px mỗi tiết

type View = 'week' | 'list'

const dayOf = (item: ScheduleItem) => (item.weekday === 1 ? 8 : item.weekday ?? 0)
const periodText = (item: ScheduleItem) => (item.startPeriod === item.endPeriod ? `Tiết ${item.startPeriod}` : `Tiết ${item.startPeriod}–${item.endPeriod}`)

const columns: Column<ScheduleItem>[] = [
  { key: 'course', header: 'Học phần', render: (i) => <span className="font-medium">{i.courseName}</span>, sortValue: (i) => i.courseName },
  { key: 'class', header: 'Lớp', render: (i) => <span className="font-mono text-xs text-muted">{i.classCode}</span>, sortValue: (i) => i.classCode },
  { key: 'day', header: 'Thứ', render: (i) => <span className="whitespace-nowrap">{weekdayLabel(i.weekday)}</span>, sortValue: (i) => dayOf(i) * 100 + i.startPeriod },
  { key: 'period', header: 'Tiết', render: (i) => <span className="whitespace-nowrap">{periodText(i)}</span>, sortValue: (i) => i.startPeriod },
  { key: 'weeks', header: 'Tuần học', render: (i) => <span className="whitespace-nowrap text-fg-2">{i.weeks ?? '—'}</span> },
  { key: 'room', header: 'Phòng', render: (i) => <span className="whitespace-nowrap">{i.room ?? '—'}</span>, sortValue: (i) => i.room },
  { key: 'lecturer', header: 'Giảng viên', render: (i) => <span className="whitespace-nowrap">{i.lecturer ?? '—'}</span>, sortValue: (i) => i.lecturer },
]

function WeekGrid({ items, highlightToday }: { items: ScheduleItem[]; highlightToday: boolean }) {
  const today = todayWeekday()
  const last = Math.max(12, ...items.map((i) => i.endPeriod))
  const periods = Array.from({ length: last }, (_, i) => i + 1)

  return (
    <div className="overflow-x-auto">
      <div className="grid min-w-[820px]" style={{ gridTemplateColumns: '64px repeat(7, minmax(0, 1fr))', gridTemplateRows: `40px repeat(${last}, ${ROW_H}px)` }}>
        <div className="border-b border-line bg-surface-2" />
        {WEEKDAYS.map((day, col) => (
          <div
            key={day}
            style={{ gridColumn: col + 2, gridRow: 1 }}
            className={cn('flex items-center gap-2 border-b border-l border-line bg-surface-2 px-3 text-[13px] font-medium', highlightToday && day === today && 'text-brand')}
          >
            <span className="hidden xl:inline">{weekdayLabel(day)}</span>
            <span className="xl:hidden">{SHORT_DAY[day]}</span>
            {highlightToday && day === today && <Badge variant="soft" tone="blue">Hôm nay</Badge>}
          </div>
        ))}

        {periods.map((p) => (
          <div key={p} style={{ gridColumn: 1, gridRow: p + 1 }} className={cn('px-3 pt-1 text-[11px] text-muted tabular-nums', p % 3 === 1 && p > 1 && 'border-t border-line')}>
            Tiết {p}
          </div>
        ))}
        {/* Nền cột ngày, kẻ ngang mỗi ca 3 tiết */}
        {WEEKDAYS.map((day, col) =>
          periods.map((p) => (
            <div
              key={`${day}-${p}`}
              style={{ gridColumn: col + 2, gridRow: p + 1 }}
              className={cn('border-l border-line', p % 3 === 1 && p > 1 && 'border-t', highlightToday && day === today && 'bg-brand-soft/40')}
            />
          )),
        )}

        {items.map((item) => {
          const col = WEEKDAYS.indexOf(dayOf(item))
          if (col < 0) return null
          return (
            <div
              key={`${item.classCode}-${item.weekday}-${item.startPeriod}`}
              style={{ gridColumn: col + 2, gridRow: `${item.startPeriod + 1} / ${item.endPeriod + 2}` }}
              className="z-10 m-1 flex min-h-0 flex-col overflow-hidden rounded-md border border-brand/20 border-l-[3px] border-l-brand bg-surface px-2 py-1.5 shadow-[var(--shadow)]"
              title={`${item.courseName} · ${periodText(item)} · ${item.room ?? ''}`}
            >
              <p className="line-clamp-2 text-xs leading-snug font-semibold">{item.courseName}</p>
              <p className="mt-0.5 truncate text-[11px] text-muted">{periodText(item)} · {item.room}</p>
              {item.endPeriod - item.startPeriod >= 2 && <p className="truncate text-[11px] text-muted">{item.lecturer}</p>}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function TodayList({ items }: { items: ScheduleItem[] }) {
  const today = todayWeekday()
  const classes = items.filter((i) => dayOf(i) === today).sort((a, b) => a.startPeriod - b.startPeriod)
  return (
    <Section title={`Hôm nay · ${weekdayLabel(today)}`} description={classes.length ? `${classes.length} buổi học` : 'Không có lịch học'} flush>
      {classes.length ? (
        <ul className="divide-y divide-line">
          {classes.map((c) => (
            <li key={`${c.classCode}-${c.startPeriod}`} className="flex gap-3 px-5 py-3">
              <div className="w-1 shrink-0 rounded-full bg-brand" />
              <div className="min-w-0">
                <p className="font-medium">{c.courseName}</p>
                <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
                  <span className="inline-flex items-center gap-1"><Clock size={12} />{periodText(c)}</span>
                  <span className="inline-flex items-center gap-1"><MapPin size={12} />{c.room ?? '—'}</span>
                  <span className="inline-flex items-center gap-1"><User size={12} />{c.lecturer ?? '—'}</span>
                </div>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="flex items-center gap-2 px-5 py-6 text-muted"><CalendarDays size={16} />Hôm nay bạn được nghỉ.</p>
      )}
    </Section>
  )
}

function ScheduleView({ items }: { items: ScheduleItem[] }) {
  const semesters = useMemo(() => {
    const seen = new Map<string, string>()
    items.forEach((i) => seen.set(i.semesterCode, i.semester))
    return [...seen].sort((a, b) => b[0].localeCompare(a[0]))
  }, [items])
  const [semester, setSemester] = useState(semesters[0][0])
  const [view, setView] = useState<View>('week')
  const [search, setSearch] = useState('')

  const current = items.filter((i) => i.semesterCode === semester)
  const keyword = search.trim().toLowerCase()
  const listRows = keyword
    ? current.filter((i) => `${i.courseName} ${i.classCode} ${i.room} ${i.lecturer}`.toLowerCase().includes(keyword))
    : current
  const isLatest = semester === semesters[0][0]
  const classCount = new Set(current.map((i) => i.classCode)).size

  return (
    <>
      <PageHeader
        title="Thời khóa biểu"
        description={`${semesters.find(([c]) => c === semester)?.[1]} · ${classCount} lớp học phần · ${current.length} buổi mỗi tuần`}
        actions={
          <Select
            label="Học kỳ"
            value={semester}
            onChange={setSemester}
            options={semesters.map(([code, name]) => ({ value: code, label: shortSemester(name) }))}
            className="w-44"
          />
        }
      />
      <div className="space-y-6">
        {isLatest && <TodayList items={current} />}
        <Section
          title={view === 'week' ? 'Lịch trong tuần' : 'Danh sách lớp'}
          aside={
            <Segmented<View> value={view} onChange={setView} options={[{ value: 'week', label: 'Theo tuần' }, { value: 'list', label: 'Danh sách' }]} />
          }
          toolbar={view === 'list' ? <SearchInput value={search} onChange={setSearch} placeholder="Tìm học phần, phòng, giảng viên…" className="sm:w-72" /> : undefined}
          flush
        >
          {view === 'week' ? (
            <WeekGrid items={current} highlightToday={isLatest} />
          ) : (
            <DataTable rows={listRows} columns={columns} rowKey={(i) => `${i.classCode}-${i.weekday}-${i.startPeriod}`} defaultSort={{ key: 'day', dir: 'asc' }} />
          )}
        </Section>
      </div>
    </>
  )
}

export function SchedulePage() {
  return (
    <QueryState query={useSchedule()} empty="Chưa có lịch học hoặc chưa đăng ký lớp nào.">
      {(items) => <ScheduleView items={items} />}
    </QueryState>
  )
}
