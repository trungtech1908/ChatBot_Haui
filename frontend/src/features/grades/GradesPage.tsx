import { useGrades } from '@/api/students'
import { Badge, type Tone } from '@/components/ui/Badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'

const letterTone = (letter: string | null): Tone => (letter === 'A' ? 'green' : letter === 'F' ? 'red' : 'gray')

export function GradesPage() {
  return (
    <>
      <PageHeader title="Bảng Điểm Cá Nhân" />
      <QueryState query={useGrades()} empty="Chưa có dữ liệu điểm môn học nào.">
        {(grades) => (
          <div className="overflow-x-auto rounded bg-white shadow">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-gray-100 text-xs font-bold text-gray-700 uppercase">
                <tr>
                  <th className="px-4 py-3">Mã MH</th>
                  <th className="px-4 py-3">Tên môn</th>
                  <th className="px-4 py-3 text-center">TX1</th>
                  <th className="px-4 py-3 text-center">TX2</th>
                  <th className="px-4 py-3 text-center">Giữa kỳ</th>
                  <th className="px-4 py-3 text-center">Cuối kỳ</th>
                  <th className="bg-blue-50 px-4 py-3 text-center">Tổng kết</th>
                  <th className="px-4 py-3 text-center">Điểm chữ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {grades.map((g, i) => (
                  <tr key={`${g.courseCode}-${i}`} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-blue-600">{g.courseCode}</td>
                    <td className="px-4 py-3 font-medium">{g.courseName}</td>
                    <td className="px-4 py-3 text-center">{g.tx1}</td>
                    <td className="px-4 py-3 text-center">{g.tx2}</td>
                    <td className="px-4 py-3 text-center">{g.midterm}</td>
                    <td className="px-4 py-3 text-center font-bold text-blue-600">{g.final}</td>
                    <td className="bg-blue-50 px-4 py-3 text-center font-bold">{g.total}</td>
                    <td className="px-4 py-3 text-center">
                      <Badge tone={letterTone(g.letter)}>{g.letter}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </QueryState>
    </>
  )
}
