import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

import { Sparkline } from '@/components/charts/Sparkline'
import { cn } from '@/lib/cn'

export interface Stat {
  label: string
  value: ReactNode
  icon?: LucideIcon
  note?: ReactNode
  /** Số liệu cần chú ý (nợ, trượt...): tô màu cảnh báo cho giá trị */
  alert?: boolean
  /** Chuỗi giá trị theo thời gian cho sparkline, điểm cuối là hiện tại */
  trend?: (number | null)[]
}

export function StatCard({ label, value, icon: Icon, note, alert, trend }: Stat) {
  return (
    <div className="card flex min-w-0 flex-col gap-3 p-4">
      <div className="flex items-center justify-between gap-2">
        <p className="truncate text-[13px] font-medium text-muted">{label}</p>
        {Icon && (
          <span className={cn('flex h-8 w-8 shrink-0 items-center justify-center rounded-lg', alert ? 'bg-danger-soft text-danger' : 'bg-brand-soft text-brand')}>
            <Icon size={16} strokeWidth={2} />
          </span>
        )}
      </div>
      <div className="flex items-end justify-between gap-3">
        <div className="min-w-0">
          <p className={cn('truncate text-2xl font-semibold tracking-tight', alert && 'text-danger')}>{value}</p>
          {note && <p className="mt-0.5 truncate text-xs text-muted">{note}</p>}
        </div>
        {trend && trend.filter((v) => v != null).length > 1 && <Sparkline values={trend} className="mb-1 h-8 w-20 shrink-0" />}
      </div>
    </div>
  )
}

export function StatGrid({ items, className }: { items: Stat[]; className?: string }) {
  return (
    <div className={cn('grid grid-cols-1 gap-3 sm:grid-cols-2', items.length >= 4 ? 'xl:grid-cols-4' : 'lg:grid-cols-3', className)}>
      {items.map((item) => (
        <StatCard key={item.label} {...item} />
      ))}
    </div>
  )
}
