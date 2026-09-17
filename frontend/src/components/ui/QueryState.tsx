import type { UseQueryResult } from '@tanstack/react-query'
import type { ReactNode } from 'react'

import { EmptyState } from './EmptyState'

interface Props<T> {
  query: UseQueryResult<T>
  empty?: string
  isEmpty?: (data: T) => boolean
  children: (data: T) => ReactNode
}

/** Hiển thị trạng thái đang tải / lỗi / rỗng của một query, còn lại render children. */
export function QueryState<T>({ query, empty = 'Chưa có dữ liệu.', isEmpty, children }: Props<T>) {
  if (query.isPending) {
    return <p className="py-10 text-center text-sm text-muted">Đang tải dữ liệu…</p>
  }
  if (query.isError) {
    return (
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-accent/40 bg-surface px-4 py-3 text-sm">
        <span className="text-accent">Không tải được dữ liệu: {query.error.message}</span>
        <button onClick={() => query.refetch()} className="btn-outline py-1">Thử lại</button>
      </div>
    )
  }
  const data = query.data
  const noData = isEmpty ? isEmpty(data) : Array.isArray(data) && data.length === 0
  return noData ? <EmptyState message={empty} /> : children(data)
}
