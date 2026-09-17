import type { UseQueryResult } from '@tanstack/react-query'
import type { ReactNode } from 'react'

import { EmptyState } from './EmptyState'

interface Props<T> {
  query: UseQueryResult<T>
  empty?: string
  isEmpty?: (data: T) => boolean
  children: (data: T) => ReactNode
}

function Loading() {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="card h-[84px] animate-pulse bg-surface-2" />
        ))}
      </div>
      <div className="card h-64 animate-pulse bg-surface-2" />
    </div>
  )
}

/** Hiển thị trạng thái đang tải / lỗi / rỗng của một query, còn lại render children. */
export function QueryState<T>({ query, empty = 'Chưa có dữ liệu.', isEmpty, children }: Props<T>) {
  if (query.isPending) return <Loading />
  if (query.isError) {
    return (
      <div className="card flex flex-wrap items-center justify-between gap-3 px-5 py-4">
        <div>
          <p className="font-medium">Không tải được dữ liệu</p>
          <p className="text-[13px] text-muted">{query.error.message}</p>
        </div>
        <button onClick={() => query.refetch()} className="btn-secondary">Thử lại</button>
      </div>
    )
  }
  const data = query.data
  const noData = isEmpty ? isEmpty(data) : Array.isArray(data) && data.length === 0
  return noData ? <EmptyState message={empty} /> : children(data)
}
