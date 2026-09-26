import { ChevronDown } from 'lucide-react'

import { cn } from '@/lib/cn'

export interface SelectOption<T extends string> {
  value: T
  label: string
}

/** Ô chọn dùng select gốc của trình duyệt (bàn phím, di động hoạt động sẵn). */
export function Select<T extends string>({ value, onChange, options, label, className }: {
  value: T
  onChange: (value: T) => void
  options: SelectOption<T>[]
  /** Nhãn cho trình đọc màn hình */
  label: string
  className?: string
}) {
  return (
    <label className={cn('relative inline-flex', className)}>
      <span className="sr-only">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as T)}
        className="input h-9 w-full cursor-pointer appearance-none pr-8 font-medium text-fg-2"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      <ChevronDown size={15} className="pointer-events-none absolute top-1/2 right-2.5 -translate-y-1/2 text-muted" />
    </label>
  )
}
