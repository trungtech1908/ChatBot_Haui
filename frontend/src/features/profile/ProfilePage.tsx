import { GraduationCap, Info, Landmark, ShieldCheck } from 'lucide-react'

import { useProfile } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { InfoRow } from '@/components/ui/InfoRow'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { formatDate } from '@/lib/format'
import type { Policy } from '@/types/student'

function PolicyBadges({ policy }: { policy: Policy }) {
  const badges = [
    policy.poorHousehold && <Badge key="poor" tone="red">Hộ nghèo</Badge>,
    policy.nearPoorHousehold && <Badge key="near" tone="orange">Hộ cận nghèo</Badge>,
    policy.orphan && <Badge key="orphan">Mồ côi</Badge>,
    policy.disabled && <Badge key="disabled" tone="purple">Khuyết tật</Badge>,
  ].filter(Boolean)
  return <>{badges.length ? badges : <Badge tone="green">Không thuộc diện chính sách</Badge>}</>
}

export function ProfilePage() {
  return (
    <>
      <PageHeader title="Hồ sơ Sinh viên" />
      <QueryState query={useProfile()}>
        {(sv) => (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <Card className="border-t-4 border-blue-600 p-6 text-center">
              <div className="mx-auto mb-4 flex h-32 w-32 items-center justify-center rounded-full border-4 border-white bg-blue-100 shadow-sm">
                <GraduationCap className="text-blue-500" size={56} />
              </div>
              <h3 className="mb-1 text-xl font-bold text-gray-800">{sv.fullName}</h3>
              <p className="mb-4 font-mono text-gray-500">{sv.studentId}</p>
              <div className="mt-6 space-y-3 border-t pt-4 text-left">
                <InfoRow label="Ngành học">{sv.major ?? 'Chưa cập nhật'}</InfoRow>
                <InfoRow label="Khóa học">{sv.cohort}</InfoRow>
                <InfoRow label="Khoa quản lý">
                  <span className="inline-flex items-center gap-1 text-purple-700">
                    <Landmark size={16} /> {sv.faculty ?? 'Chưa cập nhật'}
                  </span>
                </InfoRow>
              </div>
            </Card>

            <div className="space-y-6 lg:col-span-2">
              <Card className="p-6">
                <h4 className="mb-4 flex items-center gap-2 text-lg font-bold text-gray-700">
                  <Info className="text-blue-500" size={20} /> Thông tin cá nhân
                </h4>
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                  <InfoRow label="Ngày sinh">{formatDate(sv.dateOfBirth)}</InfoRow>
                  <InfoRow label="Số điện thoại">{sv.phone}</InfoRow>
                  <InfoRow label="Email">{sv.email}</InfoRow>
                  <InfoRow label="Địa chỉ liên hệ">{sv.address}</InfoRow>
                </div>
              </Card>

              <Card className="p-6">
                <h4 className="mb-4 flex items-center gap-2 text-lg font-bold text-gray-700">
                  <ShieldCheck className="text-green-500" size={20} /> Đối tượng & Chính sách
                </h4>
                {sv.policy ? (
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="flex justify-between rounded bg-gray-50 p-3 text-sm">
                      <span>Dân tộc</span> <span className="font-bold">{sv.policy.ethnicity}</span>
                    </div>
                    <div className="flex justify-between rounded bg-gray-50 p-3 text-sm">
                      <span>Quốc tịch</span> <span className="font-bold">{sv.policy.nationality}</span>
                    </div>
                    <div className="flex flex-wrap gap-2 md:col-span-2">
                      <PolicyBadges policy={sv.policy} />
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-500 italic">Chưa cập nhật thông tin đối tượng.</p>
                )}
              </Card>
            </div>
          </div>
        )}
      </QueryState>
    </>
  )
}
