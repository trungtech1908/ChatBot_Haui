import type { ReactNode } from 'react'

import { cn } from '@/lib/cn'

interface SectionProps {
  title?: ReactNode
  description?: ReactNode
  aside?: ReactNode
  /** Hàng bộ lọc nằm dưới tiêu đề, trên nội dung */
  toolbar?: ReactNode
  className?: string
  flush?: boolean // bỏ padding thân, dùng cho bảng/danh sách
  children: ReactNode
}

export function Section({ title, description, aside, toolbar, className, flush, children }: SectionProps) {
  return (
    <section className={cn('card min-w-0 overflow-hidden', className)}>
      {title && (
        <header className={cn('flex flex-wrap justify-between gap-3 px-5 pt-4 pb-3', description ? 'items-start' : 'items-center')}>
          <div className="min-w-0">
            <h2 className="text-[15px] font-semibold">{title}</h2>
            {description && <p className="mt-0.5 text-[13px] text-muted">{description}</p>}
          </div>
          {aside}
        </header>
      )}
      {toolbar && <div className={cn('flex flex-wrap items-center gap-2 px-5 pb-3', !title && 'pt-4')}>{toolbar}</div>}
      <div className={cn(flush ? (title || toolbar ? 'border-t border-line' : undefined) : title || toolbar ? 'px-5 pb-5' : 'p-5')}>{children}</div>
    </section>
  )
}
