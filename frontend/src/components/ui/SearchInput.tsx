import { Search } from 'lucide-react'

import { cn } from '@/lib/cn'

export function SearchInput({ value, onChange, placeholder, className }: {
  value: string
  onChange: (value: string) => void
  placeholder: string
  className?: string
}) {
  return (
    <label className={cn('relative block w-full sm:w-60', className)}>
      <Search size={15} className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-muted" />
      <input type="search" value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="input pl-9" aria-label={placeholder} />
    </label>
  )
}
