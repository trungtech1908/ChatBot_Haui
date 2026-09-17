import type { UseQueryResult } from '@tanstack/react-query'
import type { LucideIcon } from 'lucide-react'
import { AlertTriangle, RotateCw } from 'lucide-react'
import type { ReactNode } from 'react'

import { EmptyState } from './EmptyState'
import { PageSkeleton } from './Skeleton'

interface Props<T> {
  query: UseQueryResult<T>
  empty?: string
  emptyIcon?: LucideIcon
  isEmpty?: (data: T) => boolean
  skeleton?: ReactNode
  children: (data: T) => ReactNode
}

/** Hiển thị loading / lỗi / rỗng cho một query, còn lại render children. */
export function QueryState<T>({ query, empty = 'Chưa có dữ liệu.', emptyIcon, isEmpty, skeleton, children }: Props<T>) {
  if (query.isPending) return skeleton ?? <PageSkeleton />
  if (query.isError) {
    return (
      <div className="flex flex-col items-start gap-3 rounded-2xl border border-rose-500/25 bg-rose-500/5 p-5 text-rose-700 sm:flex-row sm:items-center dark:text-rose-400">
        <AlertTriangle size={20} className="shrink-0" />
        <p className="flex-1 text-sm">{query.error.message}</p>
        <button onClick={() => query.refetch()} className="btn-ghost py-1.5 text-rose-700 dark:text-rose-400">
          <RotateCw size={14} /> Thử lại
        </button>
      </div>
    )
  }
  const data = query.data
  const noData = isEmpty ? isEmpty(data) : Array.isArray(data) && data.length === 0
  return noData ? <EmptyState message={empty} icon={emptyIcon} /> : children(data)
}
