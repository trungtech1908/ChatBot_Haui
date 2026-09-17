import type { ReactNode } from 'react'

import { cn } from '@/lib/cn'

/** Danh sách nhãn - giá trị dạng bảng thông tin. */
export function DataList({ items, columns = 1 }: { items: [string, ReactNode][]; columns?: 1 | 2 }) {
  const twoColLastRow = columns === 2 && items.length % 2 === 0
  return (
    <dl className={cn('grid gap-x-8', columns === 2 && 'sm:grid-cols-2')}>
      {items.map(([label, value], i) => (
        <div
          key={label}
          className={cn(
            'flex gap-4 border-b border-dashed border-line py-2',
            i === items.length - 1 && 'border-b-0',
            twoColLastRow && i === items.length - 2 && 'sm:border-b-0',
          )}
        >
          <dt className="w-32 shrink-0 text-sm text-muted">{label}</dt>
          <dd className="min-w-0 text-sm break-words">{value || '—'}</dd>
        </div>
      ))}
    </dl>
  )
}
