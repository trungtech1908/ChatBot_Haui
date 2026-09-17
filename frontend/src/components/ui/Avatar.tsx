import { cn } from '@/lib/cn'
import { initials } from '@/lib/format'

export function Avatar({ name, className }: { name: string | null | undefined; className?: string }) {
  return (
    <span
      className={cn(
        'flex shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 font-semibold text-white',
        className ?? 'h-9 w-9 text-sm',
      )}
    >
      {initials(name)}
    </span>
  )
}
