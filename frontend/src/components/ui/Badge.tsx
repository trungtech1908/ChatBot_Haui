import type { ReactNode } from 'react'

import { cn } from '@/lib/cn'
import type { Tone } from '@/types/ui'

const tones: Record<Tone, string> = {
  gray: 'text-muted border-line',
  green: 'text-emerald-700 border-emerald-700/30 dark:text-emerald-400 dark:border-emerald-400/30',
  blue: 'text-brand border-brand/30',
  yellow: 'text-amber-700 border-amber-700/30 dark:text-amber-400 dark:border-amber-400/30',
  orange: 'text-orange-700 border-orange-700/30 dark:text-orange-400 dark:border-orange-400/30',
  red: 'text-accent border-accent/30',
  purple: 'text-violet-700 border-violet-700/30 dark:text-violet-400 dark:border-violet-400/30',
}

/** Nhãn trạng thái dạng chữ có viền mảnh. */
export function Badge({ tone = 'gray', className, children }: { tone?: Tone; className?: string; children: ReactNode }) {
  return (
    <span className={cn('inline-block rounded-sm border px-1.5 py-px text-xs font-medium whitespace-nowrap', tones[tone], className)}>
      {children}
    </span>
  )
}
