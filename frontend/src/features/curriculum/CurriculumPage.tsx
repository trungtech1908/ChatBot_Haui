import { GraduationCap, Layers } from 'lucide-react'

import { useCurriculum } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'

export function CurriculumPage() {
  return (
    <>
      <PageHeader title="Khung Chương trình Đào tạo" />
      <QueryState query={useCurriculum()}>
        {(ct) => (
          <>
            <div className="mb-6 flex items-center justify-between rounded-lg border border-blue-200 bg-blue-50 p-4 shadow-sm">
              <div>
                <p className="flex items-center gap-2 text-lg font-bold text-blue-900">
                  <GraduationCap size={20} /> Ngành: {ct.major}
                </p>
                <p className="mt-1 ml-7 text-sm text-gray-600">
                  Khóa: <span className="font-semibold">{ct.cohort}</span>
                </p>
              </div>
              <span className="rounded-full bg-blue-600 px-3 py-1 text-sm font-bold text-white shadow">
                {ct.requiredCredits} tín chỉ
              </span>
            </div>

            <div className="space-y-6">
              {ct.groups.map((group) => (
                <div key={group.code} className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-md">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-200 bg-gray-100 p-3">
                    <h3 className="flex items-center gap-2 text-lg font-bold text-gray-800">
                      <Layers className="text-blue-500" size={18} /> {group.name}
                    </h3>
                    <div className="flex gap-2">
                      {group.requiredCredits && <Badge tone="blue">Yêu cầu: {group.requiredCredits} tín chỉ</Badge>}
                      <Badge>{group.courses.length} môn</Badge>
                    </div>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                      <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase">
                        <tr>
                          <th className="px-4 py-2 text-left whitespace-nowrap">Mã môn học</th>
                          <th className="px-4 py-2 text-left">Tên môn học</th>
                          <th className="px-4 py-2 text-center whitespace-nowrap">Số TC</th>
                          <th className="px-4 py-2 text-center">Kỳ</th>
                          <th className="px-4 py-2 text-center">Loại</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {group.courses.map((course) => (
                          <tr key={course.code} className="hover:bg-blue-50">
                            <td className="px-4 py-3 font-mono font-bold whitespace-nowrap text-blue-600">{course.code}</td>
                            <td className="px-4 py-3 font-medium text-gray-800">{course.name}</td>
                            <td className="px-4 py-3 text-center font-semibold">{course.credits}</td>
                            <td className="px-4 py-3 text-center">
                              <span className="inline-block h-6 w-6 rounded-full bg-gray-200 text-xs leading-6 font-bold">
                                {course.semester}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-center">
                              {group.type === 'Bắt buộc' ? <Badge tone="red">Bắt buộc</Badge> : <Badge tone="green">Tự chọn</Badge>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </QueryState>
    </>
  )
}
