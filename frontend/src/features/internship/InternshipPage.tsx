import { useInternships } from '@/api/students'
import { DataList } from '@/components/ui/DataList'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'
import { Section } from '@/components/ui/Section'

export function InternshipPage() {
  return (
    <>
      <PageHeader section="Học tập" title="Thực tập doanh nghiệp" />
      <QueryState query={useInternships()} empty="Bạn chưa đăng ký thực tập doanh nghiệp.">
        {(internships) => (
          <div className="space-y-5">
            {internships.map((item, i) => (
              <Section key={i} title={item.company}>
                <DataList
                  columns={2}
                  items={[
                    ['Vị trí thực tập', item.position],
                    ['Giảng viên hướng dẫn', item.supervisor],
                    ['Địa chỉ', item.address],
                    ['Email doanh nghiệp', item.companyEmail && <a key="email" href={`mailto:${item.companyEmail}`} className="link">{item.companyEmail}</a>],
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
