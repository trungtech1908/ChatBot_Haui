import { CalendarX, Clock, MapPin, PenLine } from 'lucide-react'

import { useExams } from '@/api/students'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { formatDateTime } from '@/lib/format'

export function ExamsPage() {
  return (
    <>
      <PageHeader title="Lịch Thi" />
      <QueryState query={useExams()} empty="Chưa có lịch thi." emptyIcon={CalendarX}>
        {(exams) => (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {exams.map((exam) => (
              <div key={exam.candidateNumber} className="rounded border-l-4 border-purple-500 bg-white p-4 shadow">
                <h3 className="mb-1 text-lg font-bold text-gray-800">Số báo danh: {exam.candidateNumber}</h3>
                <p className="mb-2 text-sm text-gray-500">
                  Mã ca thi: <span className="font-mono">{exam.examCode}</span>
                </p>
                <div className="space-y-1 text-sm">
                  <p className="flex items-center gap-2"><Clock size={16} className="text-gray-400" /> {formatDateTime(exam.startTime)}</p>
                  <p className="flex items-center gap-2"><MapPin size={16} className="text-gray-400" /> Phòng: {exam.room} ({exam.seat})</p>
                  <p className="flex items-center gap-2"><PenLine size={16} className="text-gray-400" /> {exam.format}</p>
                </div>
                {!exam.eligible && (
                  <div className="mt-2 rounded bg-red-100 p-1 text-center text-xs font-bold text-red-600">Không đủ điều kiện thi</div>
                )}
              </div>
            ))}
          </div>
        )}
      </QueryState>
    </>
  )
}
