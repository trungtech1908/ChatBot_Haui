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

/** Nhãn trạng thái: chấm màu + chữ. */
export function Badge({ tone = 'gray', className, children }: { tone?: Tone; className?: string; children: ReactNode }) {
  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-md border border-line bg-surface px-2 py-0.5 text-xs font-medium whitespace-nowrap', className)}>
      <span className={cn('h-1.5 w-1.5 rounded-full', dots[tone])} />
      {children}
    </span>
  )
}
