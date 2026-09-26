import type { ReactNode } from 'react'

import { cn } from '@/lib/cn'

export interface SegmentOption<T extends string> {
  value: T
  label: ReactNode
  count?: number
}

/** Nhóm chip chọn một (lọc nhanh theo trạng thái). */
export function Segmented<T extends string>({ value, onChange, options, className }: {
  value: T
  onChange: (value: T) => void
  options: SegmentOption<T>[]
  className?: string
}) {
  return (
    <div role="tablist" className={cn('inline-flex max-w-full overflow-x-auto rounded-lg border border-line bg-surface-2 p-0.5', className)}>
      {options.map((option) => {
        const active = option.value === value
        return (
          <button
            key={option.value}
            role="tab"
            aria-selected={active}
            onClick={() => onChange(option.value)}
            className={cn(
              'inline-flex h-7 shrink-0 items-center gap-1.5 rounded-md px-2.5 text-[13px] font-medium whitespace-nowrap transition',
              active ? 'bg-surface text-fg shadow-[var(--shadow)] ring-1 ring-line' : 'text-muted hover:text-fg',
            )}
          >
            {option.label}
            {option.count != null && (
              <span className={cn('rounded px-1 text-[11px] tabular-nums', active ? 'bg-brand-soft text-brand-ink' : 'bg-hover text-muted')}>
                {option.count}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
