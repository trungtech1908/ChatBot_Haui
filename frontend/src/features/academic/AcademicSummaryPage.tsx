import { BarChart3, Check, GraduationCap, X } from 'lucide-react'

import { useAcademicSummary } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { classifyGpa } from '@/lib/format'
import type { Graduation } from '@/types/student'

const gpaText = { green: 'text-green-600', blue: 'text-blue-600', yellow: 'text-yellow-600', orange: 'text-orange-600', red: 'text-red-600', gray: 'text-gray-600' }

function Requirement({ ok, label }: { ok: boolean; label: string }) {
  return (
    <Badge tone={ok ? 'green' : 'gray'}>
      {ok ? <Check size={14} /> : <X size={14} />} {label}
    </Badge>
  )
}

function GraduationCard({ graduation }: { graduation: Graduation }) {
  return (
    <div className="mt-4 flex flex-col items-center justify-between gap-4 rounded-xl border border-orange-200 bg-gradient-to-br from-yellow-50 to-orange-50 p-6 shadow-md md:col-span-2 md:flex-row lg:col-span-3">
      <div className="flex items-center gap-4">
        <div className="rounded-full bg-orange-100 p-4 text-orange-600">
          <GraduationCap size={32} />
        </div>
        <div>
          <h3 className="text-xl font-bold text-gray-800">Tiến độ Tốt nghiệp</h3>
          <p className="text-sm text-gray-600">
            GPA tích lũy toàn khóa: <span className="text-lg font-bold text-orange-600">{graduation.gpa}</span>
          </p>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        <Requirement ok={graduation.creditsOk} label="Tín chỉ" />
        <Requirement ok={graduation.physicalEducationOk} label="GDTC" />
        <Requirement ok={graduation.defenseEducationOk} label="GDQP" />
        <Requirement ok={graduation.languageOk} label="Ngoại ngữ" />
      </div>
    </div>
  )
}

export function AcademicSummaryPage() {
  return (
    <>
      <PageHeader title="Tổng kết Học kỳ & Tốt nghiệp" />
      <QueryState
        query={useAcademicSummary()}
        empty="Chưa có dữ liệu tổng kết học kỳ."
        emptyIcon={BarChart3}
        isEmpty={(data) => !data.semesters.length && !data.graduation}
      >
        {({ semesters, graduation }) => (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {semesters.map((hk) => {
              const rank = classifyGpa(hk.gpa)
              return (
                <div key={hk.semester} className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-md transition-shadow hover:shadow-xl">
                  <div className="flex items-center justify-between bg-gradient-to-r from-blue-600 to-blue-800 p-4 text-white">
                    <div>
                      <h3 className="text-lg font-bold uppercase">Học kỳ {hk.semester}</h3>
                      <span className="text-xs text-blue-200">{hk.courseCount} môn đã học</span>
                    </div>
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white text-lg font-bold text-blue-800 shadow">
                      {hk.semester}
                    </div>
                  </div>
                  <div className="space-y-4 p-5 text-sm">
                    <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                      <span className="font-medium text-gray-600">Điểm TBC học kỳ</span>
                      <span className={`text-2xl font-bold ${gpaText[rank.tone]}`}>{hk.gpa}</span>
                    </div>
                    <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                      <span className="font-medium text-gray-600">Tổng tín chỉ HK</span>
                      <span className="font-bold text-gray-800">{hk.credits}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-600">Xếp loại</span>
                      <Badge tone={rank.tone}>{rank.label}</Badge>
                    </div>
                  </div>
                </div>
              )
            })}
            {graduation && <GraduationCard graduation={graduation} />}
          </div>
        )}
      </QueryState>
    </>
  )
}
