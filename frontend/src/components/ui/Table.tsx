import type { ComponentProps } from 'react'

import { cn } from '@/lib/cn'

export function Table({ className, ...props }: ComponentProps<'table'>) {
  return (
    <div className="overflow-x-auto">
      <table className={cn('w-full text-sm', className)} {...props} />
    </div>
  )
}

export const THead = ({ className, ...props }: ComponentProps<'thead'>) => (
  <thead className={cn('bg-surface-2/60 text-left text-xs font-semibold tracking-wide text-muted uppercase', className)} {...props} />
)

export const TH = ({ className, ...props }: ComponentProps<'th'>) => (
  <th className={cn('px-4 py-3 whitespace-nowrap', className)} {...props} />
)

export const TBody = ({ className, ...props }: ComponentProps<'tbody'>) => (
  <tbody className={cn('divide-y divide-line', className)} {...props} />
)

export const TR = ({ className, ...props }: ComponentProps<'tr'>) => (
  <tr className={cn('transition-colors hover:bg-surface-2/60', className)} {...props} />
)

export const TD = ({ className, ...props }: ComponentProps<'td'>) => <td className={cn('px-4 py-3', className)} {...props} />
