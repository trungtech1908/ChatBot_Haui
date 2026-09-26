import { cn } from '@/lib/cn'

/** Xu hướng nhỏ trong ô số liệu: đường màu nhạt, điểm hiện tại màu nhấn. */
export function Sparkline({ values, className }: { values: (number | null)[]; className?: string }) {
  const points = values.map((v, i) => [i, v] as const).filter((p): p is readonly [number, number] => p[1] != null)
  if (points.length < 2) return null
  const w = 80
  const h = 32
  const pad = 4
  const ys = points.map((p) => p[1])
  const min = Math.min(...ys)
  const max = Math.max(...ys)
  const x = (i: number) => pad + (i / (values.length - 1)) * (w - pad * 2)
  const y = (v: number) => (max === min ? h / 2 : pad + (1 - (v - min) / (max - min)) * (h - pad * 2))
  const last = points[points.length - 1]
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className={cn('overflow-visible', className)} aria-hidden>
      <polyline
        points={points.map(([i, v]) => `${x(i)},${y(v)}`).join(' ')}
        fill="none"
        stroke="var(--line-strong)"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
      <circle cx={x(last[0])} cy={y(last[1])} r={3.5} fill="var(--chart-1)" stroke="var(--surface)" strokeWidth={2} />
    </svg>
  )
}
