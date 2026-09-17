import { Briefcase, Building2, Mail, MapPin, UserRound } from 'lucide-react'

import { useInternships } from '@/api/students'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { QueryState } from '@/components/ui/QueryState'

export function InternshipPage() {
  return (
    <>
      <PageHeader title="Thực tập" description="Thông tin thực tập tại doanh nghiệp" />
      <QueryState query={useInternships()} empty="Bạn chưa đăng ký thực tập doanh nghiệp." emptyIcon={Briefcase}>
        {(internships) => (
          <div className="grid gap-4 lg:grid-cols-2">
            {internships.map((item, i) => (
              <div key={i} className="rounded-2xl border border-line bg-surface p-6 shadow-sm">
                <div className="flex items-start gap-4">
                  <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-md shadow-emerald-500/20">
                    <Building2 size={26} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-lg font-semibold">{item.company}</h3>
                      <Badge tone="green">Đang thực tập</Badge>
                    </div>
                    <p className="text-sm text-muted">{item.position}</p>
                  </div>
                </div>
                <dl className="mt-5 grid gap-4 border-t border-line pt-5 text-sm sm:grid-cols-2">
                  <div className="flex items-center gap-2"><MapPin size={16} className="text-muted" /> {item.address}</div>
                  <div className="flex items-center gap-2"><UserRound size={16} className="text-muted" /> GVHD: {item.supervisor}</div>
                  <div className="flex items-center gap-2 sm:col-span-2">
                    <Mail size={16} className="text-muted" />
                    <a href={`mailto:${item.companyEmail}`} className="text-primary hover:underline">{item.companyEmail}</a>
                  </div>
                </dl>
              </div>
            ))}
          </div>
        )}
      </QueryState>
    </>
  )
}
