import { Link } from 'react-router'

import { useAcademicSummary, useCurriculum, useExams, useFinance, useProfile, useSchedule } from '@/api/students'
import { DataList } from '@/components/ui/DataList'
import { Figures } from '@/components/ui/Figures'
import { PageHeader } from '@/components/ui/PageHeader'
import { Section } from '@/components/ui/Section'
import { Table, TBody, TD, TH, THead, TR } from '@/components/ui/Table'
import { formatDateTime, formatMoney, formatPeriods, weekdayLabel } from '@/lib/format'

const more = (to: string) => (
  <Link to={to} className="text-sm link">
    Xem chi tiết
  </Link>
)

export function OverviewPage() {
  const profile = useProfile().data
  const summary = useAcademicSummary().data
  const curriculum = useCurriculum().data
  const finance = useFinance().data
  const schedule = useSchedule().data
  const exams = useExams().data

  return (
    <>
      <PageHeader title="Tổng quan" />

      <div className="space-y-5">
        <Section title="Thông tin sinh viên" aside={more('/profile')}>
          <DataList
            columns={2}
            items={[
              ['Họ và tên', profile?.fullName],
              ['Mã sinh viên', profile?.studentId],
              ['Ngành', profile?.major],
              ['Khóa', profile?.cohort],
              ['Khoa quản lý', profile?.faculty],
              ['Email', profile?.email],
            ]}
          />
        </Section>

        <Figures
          items={[
            { label: 'GPA tích lũy (hệ 4)', value: summary?.graduation?.gpa ?? '—' },
            { label: 'Tín chỉ chương trình', value: curriculum?.requiredCredits ?? '—' },
            { label: 'Công nợ học phí', value: finance ? formatMoney(finance.debt) : '—', alert: !!finance?.debt },
            { label: 'Số dư tài khoản', value: finance ? formatMoney(finance.balance) : '—' },
          ]}
        />

        <div className="grid gap-5 xl:grid-cols-5">
          <Section title="Lịch học trong tuần" aside={more('/schedule')} flush className="xl:col-span-3">
            {schedule?.length ? (
              <Table>
                <THead>
                  <tr><TH>Thứ</TH><TH>Tiết</TH><TH>Môn học</TH><TH>Phòng</TH></tr>
                </THead>
                <TBody>
                  {[...schedule].sort((a, b) => (a.weekday ?? 0) - (b.weekday ?? 0)).map((item, i) => (
                    <TR key={i}>
                      <TD className="whitespace-nowrap">{weekdayLabel(item.weekday)}</TD>
                      <TD className="whitespace-nowrap">{formatPeriods(item.periods)}</TD>
                      <TD>{item.courseName}</TD>
                      <TD>{item.room}</TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            ) : (
              <p className="px-4 py-3 text-sm text-muted">{schedule ? 'Chưa có lịch học.' : 'Đang tải…'}</p>
            )}
          </Section>

          <Section title="Lịch thi" aside={more('/exams')} flush className="xl:col-span-2">
            {exams?.length ? (
              <Table>
                <THead>
                  <tr><TH>Thời gian</TH><TH>Phòng</TH><TH>Hình thức</TH></tr>
                </THead>
                <TBody>
                  {[...exams].sort((a, b) => (a.startTime ?? '').localeCompare(b.startTime ?? '')).map((exam) => (
                    <TR key={exam.candidateNumber}>
                      <TD className="whitespace-nowrap">{formatDateTime(exam.startTime)}</TD>
                      <TD>{exam.room} ({exam.seat})</TD>
                      <TD>{exam.format}</TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            ) : (
              <p className="px-4 py-3 text-sm text-muted">{exams ? 'Chưa có lịch thi.' : 'Đang tải…'}</p>
            )}
          </Section>
        </div>
      </div>
    </>
  )
}
