import type { ComponentProps } from 'react'

import { cn } from '@/lib/cn'

export function Table({ className, ...props }: ComponentProps<'table'>) {
  return (
    <div className="overflow-x-auto">
      <table className={cn('w-full border-collapse text-sm', className)} {...props} />
    </div>
  )
}

export const THead = ({ className, ...props }: ComponentProps<'thead'>) => (
  <thead className={cn('border-b border-line bg-surface-2 text-left text-xs text-muted', className)} {...props} />
)

export const TH = ({ className, ...props }: ComponentProps<'th'>) => (
  <th className={cn('px-3 py-2 font-medium whitespace-nowrap', className)} {...props} />
)

export const TBody = ({ className, ...props }: ComponentProps<'tbody'>) => (
  <tbody className={cn('divide-y divide-line', className)} {...props} />
)

export const TR = ({ className, ...props }: ComponentProps<'tr'>) => (
  <tr className={cn('hover:bg-surface-2', className)} {...props} />
)

export const TD = ({ className, ...props }: ComponentProps<'td'>) => <td className={cn('px-3 py-2 align-top', className)} {...props} />
