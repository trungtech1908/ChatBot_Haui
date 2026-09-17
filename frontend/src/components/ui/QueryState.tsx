import type { UseQueryResult } from '@tanstack/react-query'
import type { LucideIcon } from 'lucide-react'
import { AlertCircle, Loader2 } from 'lucide-react'
import type { ReactNode } from 'react'

import { EmptyState } from './EmptyState'

interface Props<T> {
  query: UseQueryResult<T>
  empty?: string
  emptyIcon?: LucideIcon
  isEmpty?: (data: T) => boolean
  children: (data: T) => ReactNode
}

/** Hiển thị loading / lỗi / rỗng cho một query, còn lại render children. */
export function QueryState<T>({ query, empty = 'Chưa có dữ liệu.', emptyIcon, isEmpty, children }: Props<T>) {
  if (query.isPending) {
    return (
      <div className="flex justify-center p-10 text-blue-600">
        <Loader2 className="animate-spin" size={32} />
      </div>
    )
  }
  if (query.isError) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-red-300 bg-red-50 p-4 text-red-700">
        <AlertCircle size={20} /> {query.error.message}
      </div>
    )
  }
  const data = query.data
  const noData = isEmpty ? isEmpty(data) : Array.isArray(data) && data.length === 0
  return noData ? <EmptyState message={empty} icon={emptyIcon} /> : children(data)
}
