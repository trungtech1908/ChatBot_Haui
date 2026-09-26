import { cn } from '@/lib/cn'

/** Thanh tiến độ: phần đã đạt màu thương hiệu, phần còn lại là bước nhạt cùng tông. */
export function Progress({ value, max, className, tone = 'brand' }: { value: number; max: number; className?: string; tone?: 'brand' | 'success' | 'danger' }) {
  const percent = max > 0 ? Math.min(100, (value / max) * 100) : 0
  return (
    <div className={cn('h-2 overflow-hidden rounded-full bg-brand-soft', className)} role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={max}>
      <div
        className={cn('h-full rounded-full transition-[width] duration-500', tone === 'brand' && 'bg-brand', tone === 'success' && 'bg-success', tone === 'danger' && 'bg-danger')}
        style={{ width: `${percent}%` }}
      />
    </div>
  )
}
