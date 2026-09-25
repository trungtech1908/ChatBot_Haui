import { Check, Minus } from 'lucide-react'

import { useAcademicSummary, useCurriculum } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { Figures } from '@/components/ui/Figures'
import { PageHeader } from '@/components/ui/PageHeader'
import { Progress } from '@/components/ui/Progress'
import { QueryState } from '@/components/ui/QueryState'
import { Section } from '@/components/ui/Section'
import { Table, TBody, TD, TH, THead, TR } from '@/components/ui/Table'
import { cn } from '@/lib/cn'
import { classifyGpa } from '@/lib/format'

export function AcademicSummaryPage() {
  const requiredCredits = useCurriculum().data?.requiredCredits ?? 0

  return (
    <>
      <PageHeader title="Tốt nghiệp" description="Kết quả theo học kỳ và điều kiện xét tốt nghiệp" />
      <QueryState query={useAcademicSummary()} empty="Chưa có dữ liệu tổng kết học kỳ." isEmpty={(data) => !data.semesters.length && !data.graduation}>
        {({ semesters, graduation }) => {
          // Tín chỉ tích lũy do hệ thống đào tạo tính (môn học lại chỉ tính 1 lần)
          const earned = graduation?.credits ?? 0
          const requirements = graduation
            ? ([
                ['Tích lũy đủ tín chỉ', graduation.creditsOk],
                ['Chứng chỉ Giáo dục thể chất', graduation.physicalEducationOk],
                ['Chứng chỉ Giáo dục quốc phòng – an ninh', graduation.defenseEducationOk],
                ['Chuẩn đầu ra ngoại ngữ', graduation.languageOk],
              ] as const)
            : []
          const done = requirements.filter(([, ok]) => ok).length

          return (
            <div className="space-y-4">
              <Figures
                items={[
                  { label: 'GPA tích lũy', value: graduation?.gpa ?? '—', note: 'Thang điểm 4' },
                  { label: 'Xếp loại', value: classifyGpa(graduation?.gpa ?? null).label },
                  { label: 'Tín chỉ tích lũy', value: earned, note: requiredCredits ? `/ ${requiredCredits} yêu cầu` : undefined },
                  { label: 'Điều kiện đạt', value: `${done}/${requirements.length}` },
                ]}
              />

              <div className="grid gap-4 lg:grid-cols-5">
                {graduation && (
                  <Section title="Điều kiện xét tốt nghiệp" description={done === requirements.length ? 'Đã đủ điều kiện' : `Còn ${requirements.length - done} điều kiện`} className="lg:col-span-2">
                    {requiredCredits > 0 && (
                      <div className="mb-4">
                        <div className="mb-2 flex justify-between text-[13px]">
                          <span className="text-muted">Tiến độ tín chỉ</span>
                          <span className="font-medium tabular-nums">{Math.round((earned / requiredCredits) * 100)}%</span>
                        </div>
                        <Progress value={earned} max={requiredCredits} />
                      </div>
                    )}
                    <ul className="space-y-2.5">
                      {requirements.map(([label, ok]) => (
                        <li key={label} className="flex items-center gap-2.5">
                          <span className={cn('flex h-5 w-5 shrink-0 items-center justify-center rounded-full', ok ? 'bg-success/15 text-success' : 'bg-hover text-muted')}>
                            {ok ? <Check size={12} strokeWidth={3} /> : <Minus size={12} strokeWidth={3} />}
                          </span>
                          <span className={ok ? '' : 'text-muted'}>{label}</span>
                        </li>
                      ))}
                    </ul>
                  </Section>
                )}

                <Section title="Kết quả theo học kỳ" flush className="lg:col-span-3">
                  <Table>
                    <THead>
                      <tr>
                        <TH>Học kỳ</TH>
                        <TH className="text-right">Học phần</TH>
                        <TH className="text-right">Tín chỉ</TH>
                        <TH className="text-right">Điểm TBC</TH>
                        <TH className="text-right">Rèn luyện</TH>
                        <TH className="text-right">Xếp loại</TH>
                      </tr>
                    </THead>
                    <TBody>
                      {semesters.map((hk) => {
                        const rank = classifyGpa(hk.gpa)
                        return (
                          <TR key={hk.code}>
                            <TD className="font-medium">
                              {hk.semester}
                              {hk.warning && <Badge tone="red" className="ml-2">Cảnh báo</Badge>}
                            </TD>
                            <TD className="text-right tabular-nums">{hk.courseCount}</TD>
                            <TD className="text-right tabular-nums">{hk.credits}</TD>
                            <TD className="text-right font-semibold tabular-nums">{hk.gpa ?? '—'}</TD>
                            <TD className="text-right tabular-nums">{hk.conductScore ?? '—'}</TD>
                            <TD className="text-right"><Badge tone={rank.tone}>{rank.label}</Badge></TD>
                          </TR>
                        )
                      })}
                    </TBody>
                  </Table>
                </Section>
              </div>
            </div>
          )
        }}
      </QueryState>
    </>
  )
}
