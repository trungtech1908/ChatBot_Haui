import type { ReactNode } from 'react'

import { cn } from '@/lib/cn'

interface SectionProps {
  title?: ReactNode
  aside?: ReactNode
  className?: string
  flush?: boolean // bỏ padding thân, dùng cho bảng
  children: ReactNode
}

export function Section({ title, aside, className, flush, children }: SectionProps) {
  return (
    <section className={cn('rounded-md border border-line bg-surface', className)}>
      {title && (
        <header className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-2.5">
          <h2 className="text-sm font-semibold">{title}</h2>
          {aside}
        </header>
      )}
      <div className={flush ? undefined : 'p-4'}>{children}</div>
    </section>
  )
}
