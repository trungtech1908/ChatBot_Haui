import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

import { cn } from '@/lib/cn'

interface CardProps {
  title?: ReactNode
  description?: ReactNode
  icon?: LucideIcon
  action?: ReactNode
  className?: string
  bodyClassName?: string
  children: ReactNode
}

export function Card({ title, description, icon: Icon, action, className, bodyClassName, children }: CardProps) {
  return (
    <section className={cn('overflow-hidden rounded-2xl border border-line bg-surface shadow-sm shadow-slate-900/[0.03]', className)}>
      {title && (
        <header className="flex items-center justify-between gap-3 border-b border-line px-5 py-4">
          <div className="flex min-w-0 items-center gap-3">
            {Icon && (
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary-soft text-primary">
                <Icon size={18} />
              </span>
            )}
            <div className="min-w-0">
              <h3 className="truncate font-semibold">{title}</h3>
              {description && <p className="truncate text-sm text-muted">{description}</p>}
            </div>
          </div>
          {action}
        </header>
      )}
      <div className={bodyClassName ?? (title ? 'p-5' : undefined)}>{children}</div>
    </section>
  )
}
