import type { LucideIcon } from 'lucide-react'
import { Cake, GraduationCap, HeartHandshake, Landmark, Mail, MapPin, Phone, School, UserRound } from 'lucide-react'
import type { ReactNode } from 'react'

import { useProfile } from '@/api/students'
import { Avatar } from '@/components/ui/Avatar'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { QueryState } from '@/components/ui/QueryState'
import { formatDate } from '@/lib/format'
import type { Policy } from '@/types/student'

function Field({ icon: Icon, label, children }: { icon: LucideIcon; label: string; children: ReactNode }) {
  return (
    <div className="flex items-start gap-3">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-surface-2 text-muted">
        <Icon size={16} />
      </span>
      <div className="min-w-0">
        <p className="text-xs text-muted">{label}</p>
        <p className="font-medium break-words">{children || '---'}</p>
      </div>
    </div>
  )
}

function PolicyBadges({ policy }: { policy: Policy }) {
  const badges = [
    policy.poorHousehold && <Badge key="poor" tone="red">Hộ nghèo</Badge>,
    policy.nearPoorHousehold && <Badge key="near" tone="orange">Hộ cận nghèo</Badge>,
    policy.orphan && <Badge key="orphan" tone="gray">Mồ côi</Badge>,
    policy.disabled && <Badge key="disabled" tone="purple">Khuyết tật</Badge>,
  ].filter(Boolean)
  return <div className="flex flex-wrap gap-2">{badges.length ? badges : <Badge tone="green">Không thuộc diện chính sách</Badge>}</div>
}

export function ProfilePage() {
  return (
    <QueryState query={useProfile()}>
      {(sv) => (
        <div className="space-y-6">
          <Card>
            <div className="h-28 bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 md:h-36" />
            <div className="flex flex-col gap-4 px-6 pb-6 sm:flex-row sm:items-end">
              <Avatar name={sv.fullName} className="-mt-12 h-24 w-24 text-3xl ring-4 ring-surface" />
              <div className="flex-1">
                <h1 className="text-2xl font-bold tracking-tight">{sv.fullName}</h1>
                <p className="font-mono text-sm text-muted">{sv.studentId}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {sv.major && <Badge tone="blue">{sv.major}</Badge>}
                {sv.cohort && <Badge tone="purple">Khóa {sv.cohort}</Badge>}
              </div>
            </div>
          </Card>

          <div className="grid gap-6 lg:grid-cols-3">
            <Card title="Thông tin cá nhân" icon={UserRound} className="lg:col-span-2">
              <div className="grid gap-5 sm:grid-cols-2">
                <Field icon={Cake} label="Ngày sinh">{formatDate(sv.dateOfBirth)}</Field>
                <Field icon={Phone} label="Số điện thoại">{sv.phone}</Field>
                <Field icon={Mail} label="Email">{sv.email}</Field>
                <Field icon={MapPin} label="Địa chỉ liên hệ">{sv.address}</Field>
              </div>
            </Card>

            <Card title="Học vụ" icon={School}>
              <div className="space-y-5">
                <Field icon={GraduationCap} label="Ngành học">{sv.major}</Field>
                <Field icon={Landmark} label="Khoa quản lý">{sv.faculty}</Field>
              </div>
            </Card>
          </div>

          <Card title="Đối tượng & chính sách" icon={HeartHandshake}>
            {sv.policy ? (
              <div className="grid gap-5 sm:grid-cols-3">
                <div>
                  <p className="text-xs text-muted">Dân tộc</p>
                  <p className="font-medium">{sv.policy.ethnicity || '---'}</p>
                </div>
                <div>
                  <p className="text-xs text-muted">Quốc tịch</p>
                  <p className="font-medium">{sv.policy.nationality || '---'}</p>
                </div>
                <div>
                  <p className="mb-1 text-xs text-muted">Diện chính sách</p>
                  <PolicyBadges policy={sv.policy} />
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted">Chưa cập nhật thông tin đối tượng.</p>
            )}
          </Card>
        </div>
      )}
    </QueryState>
  )
}
