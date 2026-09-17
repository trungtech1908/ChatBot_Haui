import { cn } from '@/lib/cn'

export function Progress({ value, max, className }: { value: number; max: number; className?: string }) {
  const percent = max > 0 ? Math.min(100, (value / max) * 100) : 0
  return (
    <div className={cn('h-1.5 overflow-hidden rounded-full bg-hover', className)}>
      <div className="h-full rounded-full bg-brand transition-[width] duration-500" style={{ width: `${percent}%` }} />
    </div>
  )
}
