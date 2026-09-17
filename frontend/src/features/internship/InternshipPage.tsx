import { Mail, MapPin, Presentation, UserCheck } from 'lucide-react'

import { useInternships } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'

export function InternshipPage() {
  return (
    <>
      <PageHeader title="Thông tin Thực tập" />
      <QueryState query={useInternships()} empty="Sinh viên chưa đăng ký thực tập doanh nghiệp.">
        {(internships) => (
          <div className="space-y-4">
            {internships.map((item, i) => (
              <Card key={i} className="border-t-4 border-green-500 p-6">
                <div className="mb-3 flex items-start justify-between">
                  <h3 className="text-xl font-bold text-blue-800">{item.company}</h3>
                  <Badge tone="green">Đang thực tập</Badge>
                </div>
                <div className="grid grid-cols-1 gap-4 text-sm md:grid-cols-2">
                  <p className="flex items-center gap-2"><UserCheck size={16} className="text-gray-400" /> <strong>Vị trí:</strong> {item.position}</p>
                  <p className="flex items-center gap-2"><MapPin size={16} className="text-gray-400" /> <strong>Địa chỉ:</strong> {item.address}</p>
                  <p className="flex items-center gap-2"><Presentation size={16} className="text-gray-400" /> <strong>GVHD:</strong> {item.supervisor}</p>
                  <p className="flex items-center gap-2"><Mail size={16} className="text-gray-400" /> <strong>Email DN:</strong> {item.companyEmail}</p>
                </div>
              </Card>
            ))}
          </div>
        )}
      </QueryState>
    </>
  )
}
