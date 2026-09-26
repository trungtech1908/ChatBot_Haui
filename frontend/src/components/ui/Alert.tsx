import { AlertTriangle, Info } from 'lucide-react'
import type { ReactNode } from 'react'

import { cn } from '@/lib/cn'

/** Thông báo cần chú ý: icon + chữ (không chỉ dựa vào màu). */
export function Alert({ tone = 'warning', title, children, action }: {
  tone?: 'warning' | 'danger' | 'info'
  title: ReactNode
  children?: ReactNode
  action?: ReactNode
}) {
  const Icon = tone === 'info' ? Info : AlertTriangle
  return (
    <div
      role="status"
      className={cn(
        'flex items-start gap-3 rounded-xl border px-4 py-3',
        tone === 'danger' && 'border-danger/25 bg-danger-soft',
        tone === 'warning' && 'border-warning/25 bg-warning-soft',
        tone === 'info' && 'border-brand/20 bg-brand-soft',
      )}
    >
      <Icon size={18} className={cn('mt-0.5 shrink-0', tone === 'danger' ? 'text-danger' : tone === 'warning' ? 'text-warning' : 'text-brand')} />
      <div className="min-w-0 flex-1">
        <p className="font-medium">{title}</p>
        {children && <div className="mt-0.5 text-[13px] text-fg-2">{children}</div>}
      </div>
      {action}
    </div>
  )
}
