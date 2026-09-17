import type { ReactNode } from 'react'

import { cn } from '@/lib/cn'

interface SectionProps {
  title?: ReactNode
  description?: ReactNode
  aside?: ReactNode
  className?: string
  flush?: boolean // bỏ padding thân, dùng cho bảng/danh sách
  children: ReactNode
}

export function Section({ title, description, aside, className, flush, children }: SectionProps) {
  return (
    <section className={cn('card min-w-0', className)}>
      {title && (
        <header className={cn('flex justify-between gap-3 px-5 pt-4 pb-3', description ? 'items-start' : 'items-center')}>
          <div className="min-w-0">
            <h2 className="font-semibold">{title}</h2>
            {description && <p className="mt-0.5 text-[13px] text-muted">{description}</p>}
          </div>
          {aside}
        </header>
      )}
      <div className={cn(flush ? (title ? 'border-t border-line' : undefined) : title ? 'px-5 pb-5' : 'p-5')}>{children}</div>
    </section>
  )
}
