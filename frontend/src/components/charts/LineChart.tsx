import { useState } from 'react'

import { useWidth } from './useWidth'

export interface LineSeries {
  name: string
  /** Màu nét: CSS var của slot categorical (var(--chart-1), var(--chart-2)) */
  color: string
  values: (number | null)[]
}

const M = { top: 16, right: 48, bottom: 30, left: 40 }

/** Biểu đồ đường theo thời gian, một trục y. Rê chuột: đường dóng + tooltip. */
export function LineChart({ categories, series, domain, ticks, height = 240, format = (v) => v.toFixed(2), label }: {
  categories: string[]
  series: LineSeries[]
  domain: [number, number]
  ticks: number[]
  height?: number
  format?: (value: number) => string
  /** Mô tả cho trình đọc màn hình */
  label: string
}) {
  const [ref, width] = useWidth<HTMLDivElement>()
  const [hover, setHover] = useState<number | null>(null)
  const n = categories.length
  const plotW = Math.max(0, width - M.left - M.right)
  const plotH = height - M.top - M.bottom
  const x = (i: number) => M.left + (n <= 1 ? plotW / 2 : (i / (n - 1)) * plotW)
  const y = (v: number) => M.top + (1 - (v - domain[0]) / (domain[1] - domain[0])) * plotH
  // Nhãn trục x: thưa bớt khi hẹp (mỗi nhãn cần ~72px)
  const every = Math.max(1, Math.ceil((n * 72) / Math.max(plotW, 1)))

  // Nhãn cuối đường: chỉ vẽ khi các nhãn cách nhau đủ xa, trùng thì để chú giải + tooltip gánh
  const ends = series
    .map((s) => {
      const i = s.values.findLastIndex((v) => v != null)
      return i < 0 ? null : { name: s.name, i, v: s.values[i] as number }
    })
    .filter((e) => e != null)
  const endLabelsFit = ends.every((a, ai) => ends.every((b, bi) => ai === bi || Math.abs(y(a.v) - y(b.v)) >= 14))

  const onMove = (e: React.MouseEvent<SVGRectElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const px = e.clientX - rect.left
    setHover(n <= 1 ? 0 : Math.max(0, Math.min(n - 1, Math.round((px / rect.width) * (n - 1)))))
  }

  return (
    <div className="space-y-3">
      {series.length > 1 && (
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-fg-2">
          {series.map((s) => (
            <span key={s.name} className="inline-flex items-center gap-1.5">
              <span className="h-0.5 w-4 rounded-full" style={{ background: s.color }} />
              {s.name}
            </span>
          ))}
        </div>
      )}
      <div ref={ref} className="relative">
        {width > 0 && (
          <svg width={width} height={height} role="img" aria-label={label} className="block">
            {ticks.map((t) => (
              <g key={t}>
                <line x1={M.left} x2={M.left + plotW} y1={y(t)} y2={y(t)} stroke={t === domain[0] ? 'var(--chart-axis)' : 'var(--chart-grid)'} strokeWidth={1} />
                <text x={M.left - 8} y={y(t)} dy="0.32em" textAnchor="end" className="fill-muted text-[11px] tabular-nums">{format(t)}</text>
              </g>
            ))}
            {categories.map((c, i) =>
              i % every === 0 || i === n - 1 ? (
                <text key={c + i} x={x(i)} y={height - 8} textAnchor="middle" className="fill-muted text-[11px]">{c}</text>
              ) : null,
            )}
            {hover != null && <line x1={x(hover)} x2={x(hover)} y1={M.top} y2={M.top + plotH} stroke="var(--line-strong)" strokeWidth={1} />}
            {series.map((s) => {
              const pts = s.values.map((v, i) => (v == null ? null : ([x(i), y(v)] as const)))
              const d = pts.reduce((acc, p, i) => (p ? acc + `${acc && pts[i - 1] ? 'L' : 'M'}${p[0]},${p[1]}` : acc), '')
              return (
                <g key={s.name}>
                  <path d={d} fill="none" stroke={s.color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                  {pts.map((p, i) =>
                    p ? <circle key={i} cx={p[0]} cy={p[1]} r={hover === i ? 5 : 4} fill={s.color} stroke="var(--surface)" strokeWidth={2} /> : null,
                  )}
                </g>
              )
            })}
            {endLabelsFit &&
              ends.map((e) => (
                <text key={e.name} x={x(e.i) + 9} y={y(e.v)} dy="0.32em" className="fill-fg text-[11px] font-medium tabular-nums">{format(e.v)}</text>
              ))}
            {/* Vùng bắt chuột rộng hơn nét vẽ */}
            <rect x={M.left - 12} y={M.top} width={plotW + 24} height={plotH} fill="transparent" onMouseMove={onMove} onMouseLeave={() => setHover(null)} />
          </svg>
        )}
        {hover != null && width > 0 && (
          <div
            className="pointer-events-none absolute z-10 min-w-36 rounded-lg border border-line bg-surface px-3 py-2 text-xs shadow-[var(--shadow-md)]"
            style={{ left: Math.min(x(hover) + 12, width - 160), top: M.top }}
          >
            <p className="mb-1 font-medium">{categories[hover]}</p>
            {series.map((s) => (
              <p key={s.name} className="flex items-center justify-between gap-4 text-fg-2">
                <span className="inline-flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full" style={{ background: s.color }} />
                  {s.name}
                </span>
                <span className="font-medium text-fg tabular-nums">{s.values[hover] == null ? '—' : format(s.values[hover] as number)}</span>
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
