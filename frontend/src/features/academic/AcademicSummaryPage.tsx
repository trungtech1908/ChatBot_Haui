import { useAcademicSummary } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { Figures } from '@/components/ui/Figures'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { Section } from '@/components/ui/Section'
import { Table, TBody, TD, TH, THead, TR } from '@/components/ui/Table'
import { classifyGpa } from '@/lib/format'

export function AcademicSummaryPage() {
  return (
    <>
      <PageHeader section="Học tập" title="Tổng kết & điều kiện tốt nghiệp" />
      <QueryState
        query={useAcademicSummary()}
        empty="Chưa có dữ liệu tổng kết học kỳ."
        isEmpty={(data) => !data.semesters.length && !data.graduation}
      >
        {({ semesters, graduation }) => {
          const requirements = graduation
            ? [
                ['Tích lũy đủ số tín chỉ', graduation.creditsOk],
                ['Chứng chỉ Giáo dục thể chất', graduation.physicalEducationOk],
                ['Chứng chỉ Giáo dục quốc phòng – an ninh', graduation.defenseEducationOk],
                ['Chuẩn đầu ra ngoại ngữ', graduation.languageOk],
              ] as const
            : []
          const done = requirements.filter(([, ok]) => ok).length

          return (
            <div className="space-y-5">
              {graduation && (
                <Figures
                  items={[
                    { label: 'GPA tích lũy (hệ 4)', value: graduation.gpa ?? '—' },
                    { label: 'Xếp loại học lực', value: <span className="text-base">{classifyGpa(graduation.gpa).label}</span> },
                    { label: 'Điều kiện tốt nghiệp', value: `${done}/${requirements.length}`, note: done === requirements.length ? 'Đã đủ điều kiện' : 'Chưa đủ điều kiện' },
                  ]}
                />
              )}

              <div className="grid gap-5 lg:grid-cols-2">
                {graduation && (
                  <Section title="Điều kiện xét tốt nghiệp" flush>
                    <Table>
                      <THead>
                        <tr><TH>Điều kiện</TH><TH className="text-right">Trạng thái</TH></tr>
                      </THead>
                      <TBody>
                        {requirements.map(([label, ok]) => (
                          <TR key={label}>
                            <TD>{label}</TD>
                            <TD className="text-right">{ok ? <Badge tone="green">Đạt</Badge> : <Badge tone="red">Chưa đạt</Badge>}</TD>
                          </TR>
                        ))}
                      </TBody>
                    </Table>
                  </Section>
                )}

                <Section title="Kết quả theo học kỳ" flush>
                  {semesters.length ? (
                    <Table>
                      <THead>
                        <tr>
                          <TH>Học kỳ</TH>
                          <TH className="text-right">Số học phần</TH>
                          <TH className="text-right">Tín chỉ</TH>
                          <TH className="text-right">Điểm TBC</TH>
                          <TH className="text-right">Xếp loại</TH>
                        </tr>
                      </THead>
                      <TBody>
                        {semesters.map((hk) => (
                          <TR key={hk.semester}>
                            <TD>Học kỳ {hk.semester}</TD>
                            <TD className="text-right tabular-nums">{hk.courseCount}</TD>
                            <TD className="text-right tabular-nums">{hk.credits}</TD>
                            <TD className="text-right font-semibold tabular-nums">{hk.gpa ?? '—'}</TD>
                            <TD className="text-right">{classifyGpa(hk.gpa).label}</TD>
                          </TR>
                        ))}
                      </TBody>
                    </Table>
                  ) : (
                    <p className="px-4 py-3 text-sm text-muted">Chưa có kết quả học kỳ.</p>
                  )}
                </Section>
              </div>
            </div>
          )
        }}
      </QueryState>
    </>
  )
}
