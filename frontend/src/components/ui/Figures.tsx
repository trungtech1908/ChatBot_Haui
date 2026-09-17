import type { ReactNode } from 'react'

import { cn } from '@/lib/cn'

export interface Figure {
  label: string
  value: ReactNode
  note?: ReactNode
  alert?: boolean
}

/** Các ô số liệu chính. */
export function Figures({ items, className }: { items: Figure[]; className?: string }) {
  return (
    <div className={cn('grid grid-cols-2 gap-3', items.length >= 4 ? 'lg:grid-cols-4' : 'lg:grid-cols-3', className)}>
      {items.map(({ label, value, note, alert }) => (
        <div key={label} className="card min-w-0 px-4 py-3.5">
          <p className="truncate text-[13px] text-muted">{label}</p>
          <p className={cn('mt-1 truncate text-2xl font-semibold tracking-tight tabular-nums', alert && 'text-danger')}>{value}</p>
          {note && <p className="mt-0.5 truncate text-xs text-muted">{note}</p>}
        </div>
      ))}
    </div>
  )
}
