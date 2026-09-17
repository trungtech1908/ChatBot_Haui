import { CalendarX, Clock, MapPin, PenLine, Ticket } from 'lucide-react'

import { useExams } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { cn } from '@/lib/cn'
import type { ExamItem } from '@/types/student'

function ExamCard({ exam }: { exam: ExamItem }) {
  const start = exam.startTime ? new Date(exam.startTime) : null
  const done = start ? start < new Date() : false

  return (
    <div className={cn('flex gap-4 rounded-2xl border border-line bg-surface p-4 shadow-sm transition hover:shadow-md', done && 'opacity-70')}>
      <div className="flex w-16 shrink-0 flex-col items-center justify-center rounded-xl bg-primary-soft py-2 text-primary">
        <span className="text-[11px] font-semibold uppercase">{start ? `Th ${start.getMonth() + 1}` : '--'}</span>
        <span className="text-2xl leading-none font-bold">{start?.getDate() ?? '--'}</span>
        <span className="text-[11px]">{start?.getFullYear()}</span>
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-semibold">Ca thi {exam.examCode}</p>
          {done ? <Badge>Đã thi</Badge> : <Badge tone="blue">Sắp thi</Badge>}
          {!exam.eligible && <Badge tone="red">Không đủ điều kiện</Badge>}
        </div>
        <div className="mt-2 grid gap-x-4 gap-y-1 text-sm text-muted sm:grid-cols-2">
          <p className="flex items-center gap-1.5"><Clock size={14} /> {start ? start.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) : '---'}</p>
          <p className="flex items-center gap-1.5"><MapPin size={14} /> Phòng {exam.room} · Ghế {exam.seat}</p>
          <p className="flex items-center gap-1.5"><PenLine size={14} /> {exam.format}</p>
          <p className="flex items-center gap-1.5"><Ticket size={14} /> SBD {exam.candidateNumber}</p>
        </div>
      </div>
    </div>
  )
}

export function ExamsPage() {
  return (
    <>
      <PageHeader title="Lịch thi" description="Các ca thi của bạn, sắp xếp theo thời gian" />
      <QueryState query={useExams()} empty="Chưa có lịch thi." emptyIcon={CalendarX}>
        {(exams) => (
          <div className="grid gap-4 lg:grid-cols-2">
            {[...exams]
              .sort((a, b) => (a.startTime ?? '').localeCompare(b.startTime ?? ''))
              .map((exam) => (
                <ExamCard key={exam.candidateNumber} exam={exam} />
              ))}
          </div>
        )}
      </QueryState>
    </>
  )
}
