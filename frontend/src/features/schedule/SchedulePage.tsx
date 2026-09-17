import { CalendarX, Clock, MapPin, UserRound } from 'lucide-react'

import { useSchedule } from '@/api/students'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { cn } from '@/lib/cn'
import { formatPeriods, weekdayLabel } from '@/lib/format'
import type { ScheduleItem } from '@/types/student'

const WEEKDAYS = [2, 3, 4, 5, 6, 7, 8]
const ACCENTS = ['border-l-blue-500', 'border-l-violet-500', 'border-l-emerald-500', 'border-l-amber-500', 'border-l-rose-500', 'border-l-cyan-500']

// Cùng một môn luôn cùng màu
const accentFor = (code: string) => ACCENTS[[...code].reduce((sum, ch) => sum + ch.charCodeAt(0), 0) % ACCENTS.length]
const startPeriod = (item: ScheduleItem) => Number(item.periods?.match(/\d+/)?.[0] ?? 0)
const normalizeDay = (weekday: number | null) => (weekday === 1 ? 8 : weekday)

function ClassCard({ item }: { item: ScheduleItem }) {
  return (
    <div className={cn('rounded-xl border border-l-4 border-line bg-surface p-3 shadow-sm transition hover:shadow-md', accentFor(item.classCode))}>
      <p className="text-sm leading-snug font-semibold">{item.courseName}</p>
      <p className="mt-0.5 font-mono text-xs text-muted">{item.classCode}</p>
      <div className="mt-2 space-y-1 text-xs text-muted">
        <p className="flex items-center gap-1.5"><Clock size={12} /> {formatPeriods(item.periods)}</p>
        <p className="flex items-center gap-1.5"><MapPin size={12} /> Phòng {item.room}</p>
        <p className="flex items-center gap-1.5"><UserRound size={12} /> {item.lecturer}</p>
      </div>
    </div>
  )
}

export function SchedulePage() {
  return (
    <>
      <PageHeader title="Lịch học" description="Thời khóa biểu các lớp đã đăng ký trong tuần" />
      <QueryState query={useSchedule()} empty="Chưa có lịch học hoặc chưa đăng ký lớp nào." emptyIcon={CalendarX}>
        {(items) => {
          const byDay = WEEKDAYS.map((day) => ({
            day,
            classes: items.filter((i) => normalizeDay(i.weekday) === day).sort((a, b) => startPeriod(a) - startPeriod(b)),
          }))
          return (
            <div className="grid gap-3 md:grid-cols-4 xl:grid-cols-7">
              {byDay.map(({ day, classes }) => (
                <div key={day} className={cn('rounded-2xl bg-surface-2/60 p-2', !classes.length && 'hidden md:block')}>
                  <div className="mb-2 flex items-center justify-between px-2 py-1">
                    <p className="text-sm font-semibold">{weekdayLabel(day)}</p>
                    <span className="text-xs text-muted">{classes.length} lớp</span>
                  </div>
                  <div className="space-y-2">
                    {classes.length ? (
                      classes.map((item, i) => <ClassCard key={`${item.classCode}-${i}`} item={item} />)
                    ) : (
                      <p className="px-2 py-6 text-center text-xs text-muted">Trống</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )
        }}
      </QueryState>
    </>
  )
}
