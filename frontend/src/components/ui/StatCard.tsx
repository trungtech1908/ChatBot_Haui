import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

import { cn } from '@/lib/cn'
import type { Tone } from '@/types/ui'

const iconTones: Record<Tone, string> = {
  gray: 'bg-slate-500/10 text-slate-500',
  green: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
  blue: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
  yellow: 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
  orange: 'bg-orange-500/10 text-orange-600 dark:text-orange-400',
  red: 'bg-rose-500/10 text-rose-600 dark:text-rose-400',
  purple: 'bg-violet-500/10 text-violet-600 dark:text-violet-400',
}

interface StatCardProps {
  label: string
  value: ReactNode
  icon: LucideIcon
  tone?: Tone
  hint?: ReactNode
}

export function StatCard({ label, value, icon: Icon, tone = 'blue', hint }: StatCardProps) {
  return (
    <div className="min-w-0 rounded-2xl border border-line bg-surface p-4 shadow-sm sm:p-5 shadow-slate-900/[0.03] transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs font-medium text-muted sm:text-sm">{label}</p>
        <span className={cn('flex h-8 w-8 shrink-0 items-center justify-center rounded-xl sm:h-10 sm:w-10', iconTones[tone])}>
          <Icon size={20} />
        </span>
      </div>
      <p className="mt-2 truncate text-lg font-bold tracking-tight tabular-nums sm:text-2xl">{value}</p>
      {hint && <p className="mt-1 truncate text-xs text-muted">{hint}</p>}
    </div>
  )
}
