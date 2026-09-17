import { useExams } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { Table, TBody, TD, TH, THead, TR } from '@/components/ui/Table'
import { formatDate } from '@/lib/format'

const time = (value: string | null) => (value ? new Date(value).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) : '—')

export function ExamsPage() {
  return (
    <>
      <PageHeader section="Học tập" title="Lịch thi" />
      <QueryState query={useExams()} empty="Chưa có lịch thi.">
        {(exams) => (
          <div className="rounded-md border border-line bg-surface">
            <Table>
              <THead>
                <tr>
                  <TH>Ngày thi</TH>
                  <TH>Giờ</TH>
                  <TH>Mã ca</TH>
                  <TH>Phòng</TH>
                  <TH>Vị trí</TH>
                  <TH>SBD</TH>
                  <TH>Hình thức</TH>
                  <TH>Điều kiện dự thi</TH>
                </tr>
              </THead>
              <TBody>
                {[...exams]
                  .sort((a, b) => (a.startTime ?? '').localeCompare(b.startTime ?? ''))
                  .map((exam) => (
                    <TR key={exam.candidateNumber}>
                      <TD className="whitespace-nowrap">{formatDate(exam.startTime)}</TD>
                      <TD className="tabular-nums">{time(exam.startTime)}</TD>
                      <TD className="font-mono text-xs">{exam.examCode}</TD>
                      <TD>{exam.room}</TD>
                      <TD>{exam.seat}</TD>
                      <TD className="tabular-nums">{exam.candidateNumber}</TD>
                      <TD>{exam.format}</TD>
                      <TD>{exam.eligible ? <Badge tone="green">Đủ điều kiện</Badge> : <Badge tone="red">Không đủ điều kiện</Badge>}</TD>
                    </TR>
                  ))}
              </TBody>
            </Table>
          </div>
        )}
      </QueryState>
    </>
  )
}
