import type { ReactNode } from 'react'

import { cn } from '@/lib/cn'
import type { Tone } from '@/types/ui'

const dots: Record<Tone, string> = {
  gray: 'bg-zinc-400',
  green: 'bg-success',
  blue: 'bg-brand',
  yellow: 'bg-warning',
  orange: 'bg-orange-500',
  red: 'bg-danger',
  purple: 'bg-violet-500',
}

const soft: Record<Tone, string> = {
  gray: 'bg-hover text-fg-2',
  green: 'bg-success-soft text-success',
  blue: 'bg-brand-soft text-brand-ink',
  yellow: 'bg-warning-soft text-warning',
  orange: 'bg-orange-500/12 text-orange-600 dark:text-orange-400',
  red: 'bg-danger-soft text-danger',
  purple: 'bg-violet-500/12 text-violet-600 dark:text-violet-400',
}

/** Nhãn trạng thái. dot: chấm màu + chữ (trung tính); soft: nền màu nhạt (nổi bật hơn, dùng cho điểm chữ, trạng thái). */
export function Badge({ tone = 'gray', variant = 'dot', className, title, children }: {
  tone?: Tone
  variant?: 'dot' | 'soft'
  className?: string
  title?: string
  children: ReactNode
}) {
  if (variant === 'soft') {
    return (
      <span title={title} className={cn('inline-flex items-center rounded-md px-1.5 py-0.5 text-xs font-semibold whitespace-nowrap', soft[tone], className)}>
        {children}
      </span>
    )
  }
  return (
    <span title={title} className={cn('inline-flex items-center gap-1.5 rounded-md border border-line bg-surface px-2 py-0.5 text-xs font-medium whitespace-nowrap text-fg-2', className)}>
      <span className={cn('h-1.5 w-1.5 rounded-full', dots[tone])} />
      {children}
    </span>
  )
}
