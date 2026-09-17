import type { ReactNode } from 'react'

import { cn } from '@/lib/cn'

export interface Figure {
  label: string
  value: ReactNode
  note?: ReactNode
  alert?: boolean
}

/** Hàng số liệu chính, ngăn bằng đường kẻ dọc. */
export function Figures({ items, className }: { items: Figure[]; className?: string }) {
  return (
    <dl className={cn('grid grid-cols-2 rounded-md border border-line bg-surface sm:flex sm:divide-x sm:divide-line', className)}>
      {items.map(({ label, value, note, alert }, i) => (
        <div key={label} className={cn('min-w-0 flex-1 px-4 py-3', i >= 2 && 'border-t border-line sm:border-t-0', i % 2 === 1 && 'border-l border-line sm:border-l-0')}>
          <dt className="text-xs text-muted">{label}</dt>
          <dd className={cn('mt-0.5 truncate text-xl font-semibold tabular-nums', alert && 'text-accent')}>{value}</dd>
          {note && <dd className="truncate text-xs text-muted">{note}</dd>}
        </div>
      ))}
    </dl>
  )
}
