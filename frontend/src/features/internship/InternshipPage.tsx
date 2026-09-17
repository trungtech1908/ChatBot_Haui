import { useInternships } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { DataList } from '@/components/ui/DataList'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { Section } from '@/components/ui/Section'

export function InternshipPage() {
  return (
    <>
      <PageHeader title="Thực tập" description="Thông tin thực tập tại doanh nghiệp" />
      <QueryState query={useInternships()} empty="Bạn chưa đăng ký thực tập doanh nghiệp.">
        {(internships) => (
          <div className="space-y-4">
            {internships.map((item, i) => (
              <Section key={i} title={item.company} description={item.position} aside={<Badge tone="green">Đang thực tập</Badge>}>
                <DataList
                  columns={2}
                  items={[
                    ['Giảng viên hướng dẫn', item.supervisor],
                    ['Địa chỉ', item.address],
                    ['Email doanh nghiệp', item.companyEmail && <a key="email" href={`mailto:${item.companyEmail}`} className="text-brand hover:underline">{item.companyEmail}</a>],
                  ]}
                />
              </Section>
            ))}
          </div>
        )}
      </QueryState>
    </>
  )
}
