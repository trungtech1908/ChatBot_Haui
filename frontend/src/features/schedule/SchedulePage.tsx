import { CalendarDays, Clock, MapPin, Presentation } from 'lucide-react'

import { useSchedule } from '@/api/students'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'

export function SchedulePage() {
  return (
    <>
      <PageHeader title="Lịch Học Trong Tuần" />
      <QueryState query={useSchedule()} empty="Chưa có lịch học hoặc chưa đăng ký lớp nào.">
        {(items) => (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {items.map((item, i) => (
              <div key={`${item.classCode}-${i}`} className="rounded border-l-4 border-blue-500 bg-white p-4 shadow transition-shadow hover:shadow-md">
                <h3 className="mb-1 text-lg font-bold text-gray-800">{item.courseName}</h3>
                <p className="mb-2 text-sm text-gray-500">
                  Lớp: <span className="font-mono text-blue-600">{item.classCode}</span>
                </p>
                <div className="space-y-1 text-sm">
                  <p className="flex items-center gap-2"><CalendarDays size={16} className="text-gray-400" /> <strong>Thứ:</strong> {item.weekday}</p>
                  <p className="flex items-center gap-2"><Clock size={16} className="text-gray-400" /> <strong>Tiết:</strong> {item.periods}</p>
                  <p className="flex items-center gap-2"><MapPin size={16} className="text-gray-400" /> <strong>Phòng:</strong> {item.room}</p>
                  <p className="flex items-center gap-2"><Presentation size={16} className="text-gray-400" /> <strong>GV:</strong> {item.lecturer}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </QueryState>
    </>
  )
}
