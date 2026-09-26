import { useState } from 'react'

import { useWidth } from './useWidth'

const M = { top: 20, right: 8, bottom: 28, left: 8 }

/** Biểu đồ cột một chuỗi: cột ≤ 24px, đầu bo 4px, giá trị trên đỉnh cột, rê chuột hiện tooltip. */
export function ColumnChart({ categories, values, height = 200, max, format = String, tooltip, label }: {
  categories: string[]
  values: number[]
  height?: number
  max?: number
  format?: (value: number) => string
  tooltip?: (index: number) => string
  label: string
}) {
  const [ref, width] = useWidth<HTMLDivElement>()
  const [hover, setHover] = useState<number | null>(null)
  const n = categories.length
  const plotW = Math.max(0, width - M.left - M.right)
  const plotH = height - M.top - M.bottom
  const top = max ?? Math.max(1, ...values)
  const band = n ? plotW / n : 0
  const barW = Math.min(24, band * 0.6)
  const base = M.top + plotH

  return (
    <div ref={ref} className="relative">
      {width > 0 && (
        <svg width={width} height={height} role="img" aria-label={label} className="block">
          <line x1={M.left} x2={M.left + plotW} y1={base} y2={base} stroke="var(--chart-axis)" strokeWidth={1} />
          {values.map((v, i) => {
            const cx = M.left + band * i + band / 2
            const h = (Math.max(0, v) / top) * plotH
            const x0 = cx - barW / 2
            const y0 = base - h
            const r = Math.min(4, h, barW / 2)
            const d = h > 0
              ? `M${x0},${base}V${y0 + r}Q${x0},${y0} ${x0 + r},${y0}H${x0 + barW - r}Q${x0 + barW},${y0} ${x0 + barW},${y0 + r}V${base}Z`
              : ''
            return (
              <g key={categories[i]} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}>
                {/* Vùng bắt chuột cả dải, rộng hơn cột */}
                <rect x={M.left + band * i} y={M.top} width={band} height={plotH} fill="transparent" />
                {d && <path d={d} fill="var(--chart-1)" opacity={hover == null || hover === i ? 1 : 0.55} />}
                <text x={cx} y={y0 - 6} textAnchor="middle" className="fill-fg-2 text-[11px] font-medium tabular-nums">{format(v)}</text>
                <text x={cx} y={height - 8} textAnchor="middle" className="fill-muted text-[11px]">{categories[i]}</text>
              </g>
            )
          })}
        </svg>
      )}
      {hover != null && tooltip && width > 0 && (
        <div
          className="pointer-events-none absolute z-10 rounded-lg border border-line bg-surface px-3 py-2 text-xs whitespace-nowrap shadow-[var(--shadow-md)]"
          style={{ left: Math.min(M.left + band * hover + band / 2 + 10, width - 170), top: 0 }}
        >
          {tooltip(hover)}
        </div>
      )}
    </div>
  )
}
