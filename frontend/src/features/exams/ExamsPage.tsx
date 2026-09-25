import { useExams } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { Section } from '@/components/ui/Section'
import { Table, TBody, TD, TH, THead, TR } from '@/components/ui/Table'
import { formatDate } from '@/lib/format'

const time = (value: string | null) => (value ? new Date(value).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) : '—')

export function ExamsPage() {
  return (
    <>
      <PageHeader title="Lịch thi" description="Lịch thi kết thúc học phần của bạn" />
      <QueryState query={useExams()} empty="Chưa có lịch thi.">
        {(exams) => (
          <Section title={exams[0].semester} flush>
            <Table>
              <THead>
                <tr>
                  <TH>Học phần</TH>
                  <TH>Ngày thi</TH>
                  <TH>Giờ</TH>
                  <TH>Phòng</TH>
                  <TH>Vị trí</TH>
                  <TH>SBD</TH>
                  <TH>Hình thức</TH>
                  <TH>Lớp học phần</TH>
                  <TH className="text-right">Điều kiện</TH>
                </tr>
              </THead>
              <TBody>
                {[...exams]
                  .sort((a, b) => (a.startTime ?? '').localeCompare(b.startTime ?? ''))
                  .map((exam) => (
                    <TR key={`${exam.examCode}-${exam.startTime}`}>
                      <TD className="min-w-48 font-medium">{exam.courseName}</TD>
                      <TD className="whitespace-nowrap">{formatDate(exam.startTime)}</TD>
                      <TD className="tabular-nums">{time(exam.startTime)}</TD>
                      <TD className="whitespace-nowrap">{exam.room}</TD>
                      <TD>{exam.seat}</TD>
                      <TD className="tabular-nums">{exam.candidateNumber}</TD>
                      <TD>{exam.format}</TD>
                      <TD className="font-mono text-xs text-muted">{exam.examCode}</TD>
                      <TD className="text-right">
                        {exam.eligible ? <Badge tone="green">Đủ điều kiện</Badge> : <span title={exam.ineligibleReason ?? undefined}><Badge tone="red">Không đủ</Badge></span>}
                      </TD>
                    </TR>
                  ))}
              </TBody>
            </Table>
          </Section>
        )}
      </QueryState>
    </>
  )
}
