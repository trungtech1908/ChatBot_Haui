import { ArrowDown, ArrowUp, ChevronsUpDown } from 'lucide-react'
import { type ReactNode, useMemo, useState } from 'react'

import { cn } from '@/lib/cn'

export interface Column<T> {
  key: string
  header: ReactNode
  render: (row: T) => ReactNode
  /** Có thì cột sắp xếp được; null luôn xếp cuối */
  sortValue?: (row: T) => string | number | null | undefined
  align?: 'left' | 'right' | 'center'
  className?: string
}

export interface SortState {
  key: string
  dir: 'asc' | 'desc'
}

const alignClass = { left: 'text-left', right: 'text-right', center: 'text-center' }
const collator = new Intl.Collator('vi', { numeric: true, sensitivity: 'base' })

function sortRows<T>(rows: T[], columns: Column<T>[], sort: SortState | null): T[] {
  const column = sort && columns.find((c) => c.key === sort.key)
  if (!column?.sortValue) return rows
  const get = column.sortValue
  const sign = sort?.dir === 'asc' ? 1 : -1
  return [...rows].sort((a, b) => {
    const va = get(a)
    const vb = get(b)
    if (va == null && vb == null) return 0
    if (va == null) return 1
    if (vb == null) return -1
    const cmp = typeof va === 'number' && typeof vb === 'number' ? va - vb : collator.compare(String(va), String(vb))
    return cmp * sign
  })
}

/** Bảng dữ liệu: bấm tiêu đề cột để sắp xếp (tăng → giảm). */
export function DataTable<T>({ rows, columns, rowKey, defaultSort = null, empty = 'Không có dữ liệu phù hợp.', rowClassName, dense }: {
  rows: T[]
  columns: Column<T>[]
  rowKey: (row: T, index: number) => string
  defaultSort?: SortState | null
  empty?: ReactNode
  rowClassName?: (row: T) => string | undefined
  dense?: boolean
}) {
  const [sort, setSort] = useState<SortState | null>(defaultSort)
  const sorted = useMemo(() => sortRows(rows, columns, sort), [rows, columns, sort])

  const toggle = (key: string) =>
    setSort((s) => (s?.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'asc' }))

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-line bg-surface-2">
            {columns.map((c) => {
              const active = sort?.key === c.key
              const Icon = active ? (sort.dir === 'asc' ? ArrowUp : ArrowDown) : ChevronsUpDown
              return (
                <th
                  key={c.key}
                  scope="col"
                  aria-sort={active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : undefined}
                  className={cn('h-10 px-3 text-xs font-medium whitespace-nowrap text-muted first:pl-5 last:pr-5', alignClass[c.align ?? 'left'])}
                >
                  {c.sortValue ? (
                    <button
                      onClick={() => toggle(c.key)}
                      className={cn('inline-flex items-center gap-1 rounded hover:text-fg', active && 'text-fg', c.align === 'right' && 'flex-row-reverse')}
                    >
                      {c.header}
                      <Icon size={13} className={active ? 'text-brand' : 'opacity-50'} />
                    </button>
                  ) : (
                    c.header
                  )}
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {sorted.length ? (
            sorted.map((row, i) => (
              <tr key={rowKey(row, i)} className={cn('transition-colors hover:bg-hover/60', rowClassName?.(row))}>
                {columns.map((c) => (
                  <td
                    key={c.key}
                    className={cn('px-3 first:pl-5 last:pr-5', dense ? 'h-10' : 'h-12', alignClass[c.align ?? 'left'], c.align === 'right' && 'num', c.className)}
                  >
                    {c.render(row)}
                  </td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length} className="px-5 py-10 text-center text-muted">{empty}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
