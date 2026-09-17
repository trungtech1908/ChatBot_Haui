import { useSchedule } from '@/api/students'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { weekdayLabel } from '@/lib/format'
import type { ScheduleItem } from '@/types/student'

const WEEKDAYS = [2, 3, 4, 5, 6, 7, 8]
// Ca học theo tiết: 1-3, 4-6, 7-9, 10-12, 13-15
const SLOTS = [1, 4, 7, 10, 13].map((start) => ({ start, label: `Tiết ${start}–${start + 2}` }))

const startPeriod = (item: ScheduleItem) => Number(item.periods?.match(/\d+/)?.[0] ?? 0)
const slotOf = (item: ScheduleItem) => Math.floor((startPeriod(item) - 1) / 3)
const dayOf = (item: ScheduleItem) => (item.weekday === 1 ? 8 : item.weekday)

function Timetable({ items }: { items: ScheduleItem[] }) {
  // Chỉ hiện các ca có lớp, tối thiểu 3 ca đầu cho bảng không bị cụt
  const lastSlot = Math.max(2, ...items.map(slotOf))
  const slots = SLOTS.slice(0, lastSlot + 1)

  return (
    <div className="overflow-x-auto rounded-md border border-line bg-surface">
      <table className="w-full min-w-[760px] table-fixed border-collapse text-sm">
        <thead className="bg-surface-2 text-xs text-muted">
          <tr>
            <th className="w-20 border-r border-b border-line px-2 py-2 text-left font-medium">Ca</th>
            {WEEKDAYS.map((day) => (
              <th key={day} className="border-b border-l border-line px-2 py-2 text-left font-medium first:border-l-0">
                {weekdayLabel(day)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {slots.map((slot, slotIndex) => (
            <tr key={slot.start} className="border-b border-line last:border-b-0">
              <th className="border-r border-line bg-surface-2 px-2 py-2 text-left align-top text-xs font-medium text-muted">{slot.label}</th>
              {WEEKDAYS.map((day) => {
                const classes = items.filter((i) => dayOf(i) === day && slotOf(i) === slotIndex)
                return (
                  <td key={day} className="h-20 border-l border-line p-1 align-top first:border-l-0">
                    {classes.map((item, i) => (
                      <div key={i} className="mb-1 border-l-2 border-brand bg-brand-soft px-1.5 py-1 last:mb-0">
                        <p className="text-xs leading-snug font-medium">{item.courseName}</p>
                        <p className="text-[11px] text-muted">
                          P.{item.room} · {item.classCode}
                        </p>
                      </div>
                    ))}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function SchedulePage() {
  return (
    <>
      <PageHeader section="Học tập" title="Thời khóa biểu" />
      <QueryState query={useSchedule()} empty="Chưa có lịch học hoặc chưa đăng ký lớp nào.">
        {(items) => (
          <>
            <Timetable items={items} />
            <p className="mt-2 text-xs text-muted">Giảng viên và chi tiết lớp: xem bảng bên dưới.</p>
            <div className="mt-3 overflow-x-auto rounded-md border border-line bg-surface">
              <table className="w-full text-sm">
                <thead className="border-b border-line bg-surface-2 text-left text-xs text-muted">
                  <tr>
                    <th className="px-3 py-2 font-medium">Lớp</th>
                    <th className="px-3 py-2 font-medium">Học phần</th>
                    <th className="px-3 py-2 font-medium">Lịch</th>
                    <th className="px-3 py-2 font-medium">Phòng</th>
                    <th className="px-3 py-2 font-medium">Giảng viên</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {[...items].sort((a, b) => (dayOf(a) ?? 0) - (dayOf(b) ?? 0) || startPeriod(a) - startPeriod(b)).map((item, i) => (
                    <tr key={i} className="hover:bg-surface-2">
                      <td className="px-3 py-2 font-mono text-xs whitespace-nowrap">{item.classCode}</td>
                      <td className="px-3 py-2">{item.courseName}</td>
                      <td className="px-3 py-2 whitespace-nowrap">{weekdayLabel(item.weekday)}, {item.periods?.replace(/^Tiet/i, 'tiết')}</td>
                      <td className="px-3 py-2">{item.room}</td>
                      <td className="px-3 py-2 whitespace-nowrap">{item.lecturer}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </QueryState>
    </>
  )
}
