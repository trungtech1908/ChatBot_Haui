import { useProfile } from '@/api/students'
import { DataList } from '@/components/ui/DataList'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { Section } from '@/components/ui/Section'
import { formatDate } from '@/lib/format'
import type { Policy } from '@/types/student'

function policyText(policy: Policy) {
  const groups = [
    policy.poorHousehold && 'Hộ nghèo',
    policy.nearPoorHousehold && 'Hộ cận nghèo',
    policy.orphan && 'Mồ côi',
    policy.disabled && 'Khuyết tật',
  ].filter(Boolean)
  return groups.length ? groups.join(', ') : 'Không thuộc diện chính sách'
}

export function ProfilePage() {
  return (
    <>
      <PageHeader section="Chung" title="Hồ sơ sinh viên" />
      <QueryState query={useProfile()}>
        {(sv) => (
          <div className="space-y-5">
            <Section title="Thông tin cá nhân">
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

            <Section title="Thông tin học vụ">
              <DataList
                columns={2}
                items={[
                  ['Ngành học', sv.major],
                  ['Khóa học', sv.cohort],
                  ['Khoa quản lý', sv.faculty],
                  ['Tài khoản', sv.username],
                ]}
              />
            </Section>

            <Section title="Đối tượng & chính sách">
              {sv.policy ? (
                <DataList
                  columns={2}
                  items={[
                    ['Dân tộc', sv.policy.ethnicity],
                    ['Quốc tịch', sv.policy.nationality],
                    ['Diện chính sách', policyText(sv.policy)],
                  ]}
                />
              ) : (
                <p className="text-sm text-muted">Chưa cập nhật thông tin đối tượng.</p>
              )}
            </Section>
          </div>
        )}
      </QueryState>
    </>
  )
}
