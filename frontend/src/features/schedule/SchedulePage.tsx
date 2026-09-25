import { useSchedule } from '@/api/students'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { Section } from '@/components/ui/Section'
import { Table, TBody, TD, TH, THead, TR } from '@/components/ui/Table'
import { cn } from '@/lib/cn'
import { formatPeriods, weekdayLabel } from '@/lib/format'
import type { ScheduleItem } from '@/types/student'

const WEEKDAYS = [2, 3, 4, 5, 6, 7, 8]
const SHORT_DAY: Record<number, string> = { 2: 'T2', 3: 'T3', 4: 'T4', 5: 'T5', 6: 'T6', 7: 'T7', 8: 'CN' }
// Mỗi ca 3 tiết
const SLOTS = [1, 4, 7, 10, 13]
const COLORS = [
  'border-blue-500 bg-blue-500/10',
  'border-violet-500 bg-violet-500/10',
  'border-emerald-500 bg-emerald-500/10',
  'border-amber-500 bg-amber-500/10',
  'border-rose-500 bg-rose-500/10',
  'border-cyan-500 bg-cyan-500/10',
]

const startPeriod = (item: ScheduleItem) => Number(item.periods?.match(/\d+/)?.[0] ?? 0)
const slotOf = (item: ScheduleItem) => Math.floor((startPeriod(item) - 1) / 3)
const dayOf = (item: ScheduleItem) => (item.weekday === 1 ? 8 : item.weekday)
// Cùng một lớp luôn cùng màu
const colorOf = (code: string) => COLORS[[...code].reduce((sum, ch) => sum + ch.charCodeAt(0), 0) % COLORS.length]

function WeekGrid({ items }: { items: ScheduleItem[] }) {
  const slotCount = Math.max(3, ...items.map((i) => slotOf(i) + 1))

  return (
    <div className="card overflow-x-auto">
      <div className="grid min-w-[760px] grid-cols-[72px_repeat(7,minmax(0,1fr))]">
        <div className="border-b border-line" />
        {WEEKDAYS.map((day) => (
          <div key={day} className="border-b border-l border-line px-3 py-2.5 text-[13px] font-medium">
            <span className="hidden xl:inline">{weekdayLabel(day)}</span>
            <span className="xl:hidden">{SHORT_DAY[day]}</span>
          </div>
        ))}

        {SLOTS.slice(0, slotCount).map((start, slot) => (
          <div key={start} className="contents">
            <div className={cn('px-3 py-2 text-xs text-muted tabular-nums', slot > 0 && 'border-t border-line')}>
              Tiết {start}–{start + 2}
            </div>
            {WEEKDAYS.map((day) => {
              const classes = items.filter((i) => dayOf(i) === day && slotOf(i) === slot)
              return (
                <div key={day} className={cn('min-h-24 space-y-1 border-l border-line p-1.5', slot > 0 && 'border-t')}>
                  {classes.map((item, i) => (
                    <div key={i} className={cn('rounded-md border-l-2 px-2 py-1.5', colorOf(item.classCode))}>
                      <p className="text-xs leading-snug font-medium">{item.courseName}</p>
                      <p className="mt-0.5 text-[11px] text-muted">Phòng {item.room}</p>
                    </div>
                  ))}
                </div>
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}

export function SchedulePage() {
  return (
    <QueryState query={useSchedule()} empty="Chưa có lịch học hoặc chưa đăng ký lớp nào.">
      {(items) => (
        <>
          <PageHeader title="Thời khóa biểu" description={`${items[0].semester} · ${new Set(items.map((i) => i.classCode)).size} lớp học phần trong tuần`} />
          <div className="space-y-4">
            <WeekGrid items={items} />
            <Section title="Danh sách lớp" flush>
              <Table>
                <THead>
                  <tr>
                    <TH>Học phần</TH>
                    <TH>Lớp</TH>
                    <TH>Lịch học</TH>
                    <TH>Tuần</TH>
                    <TH>Phòng</TH>
                    <TH>Giảng viên</TH>
                  </tr>
                </THead>
                <TBody>
                  {[...items].sort((a, b) => (dayOf(a) ?? 0) - (dayOf(b) ?? 0) || startPeriod(a) - startPeriod(b)).map((item, i) => (
                    <TR key={i}>
                      <TD className="font-medium">{item.courseName}</TD>
                      <TD className="font-mono text-xs text-muted">{item.classCode}</TD>
                      <TD className="whitespace-nowrap">{weekdayLabel(item.weekday)}, {formatPeriods(item.periods).toLowerCase()}</TD>
                      <TD className="whitespace-nowrap text-muted">{item.weeks ?? '—'}</TD>
                      <TD className="whitespace-nowrap">{item.room}</TD>
                      <TD className="whitespace-nowrap">{item.lecturer}</TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            </Section>
          </div>
        </>
      )}
    </QueryState>
  )
}
