import { useProfile } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { DataList } from '@/components/ui/DataList'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { Section } from '@/components/ui/Section'
import { formatDate } from '@/lib/format'
import type { Policy } from '@/types/student'

function PolicyBadges({ policy }: { policy: Policy }) {
  const groups = [
    policy.poorHousehold && 'Hộ nghèo',
    policy.nearPoorHousehold && 'Hộ cận nghèo',
    policy.orphan && 'Mồ côi',
    policy.disabled && 'Khuyết tật',
  ].filter((g): g is string => !!g)
  if (!groups.length) return <span>Không thuộc diện chính sách</span>
  return (
    <span className="flex flex-wrap gap-1.5">
      {groups.map((g) => (
        <Badge key={g} tone="orange">{g}</Badge>
      ))}
    </span>
  )
}

export function ProfilePage() {
  return (
    <QueryState query={useProfile()}>
      {(sv) => (
        <>
          <PageHeader title="Hồ sơ sinh viên" description={`${sv.fullName} · ${sv.studentId}`} />
          <div className="grid gap-4 lg:grid-cols-3">
            <Section title="Thông tin cá nhân" className="lg:col-span-2">
              <DataList
                columns={2}
                items={[
                  ['Họ và tên', sv.fullName],
                  ['Mã sinh viên', sv.studentId],
                  ['Ngày sinh', formatDate(sv.dateOfBirth)],
                  ['Số điện thoại', sv.phone],
                  ['Email', sv.email],
                  ['Địa chỉ liên hệ', sv.address],
                ]}
              />
            </Section>
            <Section title="Học vụ">
              <DataList
                items={[
                  ['Ngành học', sv.major],
                  ['Khóa học', sv.cohort],
                  ['Khoa quản lý', sv.faculty],
                ]}
              />
            </Section>
            <Section title="Đối tượng & chính sách" className="lg:col-span-3">
              {sv.policy ? (
                <DataList
                  columns={2}
                  items={[
                    ['Dân tộc', sv.policy.ethnicity],
                    ['Quốc tịch', sv.policy.nationality],
                    ['Diện chính sách', <PolicyBadges key="policy" policy={sv.policy} />],
                  ]}
                />
              ) : (
                <p className="text-muted">Chưa cập nhật thông tin đối tượng.</p>
              )}
            </Section>
          </div>
        </>
      )}
    </QueryState>
  )
}
