import type { ReactNode } from 'react'

import { cn } from '@/lib/cn'

/** Danh sách nhãn - giá trị. */
export function DataList({ items, columns = 1 }: { items: [string, ReactNode][]; columns?: 1 | 2 }) {
  return (
    <dl className={cn('grid gap-x-10 gap-y-4', columns === 2 && 'sm:grid-cols-2')}>
      {items.map(([label, value]) => (
        <div key={label} className="min-w-0">
          <dt className="text-[13px] text-muted">{label}</dt>
          <dd className="mt-0.5 font-medium break-words">{value || '—'}</dd>
        </div>
      ))}
    </dl>
  )
}
