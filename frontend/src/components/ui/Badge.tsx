import type { ReactNode } from 'react'

import { cn } from '@/lib/cn'
import type { Tone } from '@/types/ui'

const toneClasses: Record<Tone, string> = {
  gray: 'bg-slate-500/10 text-slate-600 ring-slate-500/20 dark:text-slate-300',
  green: 'bg-emerald-500/10 text-emerald-700 ring-emerald-500/25 dark:text-emerald-400',
  blue: 'bg-blue-500/10 text-blue-700 ring-blue-500/25 dark:text-blue-400',
  yellow: 'bg-amber-500/10 text-amber-700 ring-amber-500/25 dark:text-amber-400',
  orange: 'bg-orange-500/10 text-orange-700 ring-orange-500/25 dark:text-orange-400',
  red: 'bg-rose-500/10 text-rose-700 ring-rose-500/25 dark:text-rose-400',
  purple: 'bg-violet-500/10 text-violet-700 ring-violet-500/25 dark:text-violet-400',
}

export function Badge({ tone = 'gray', className, children }: { tone?: Tone; className?: string; children: ReactNode }) {
  return (
    <span className={cn('inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap ring-1 ring-inset', toneClasses[tone], className)}>
      {children}
    </span>
  )
}
