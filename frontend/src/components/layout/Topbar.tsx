import { Menu } from 'lucide-react'
import { useLocation } from 'react-router'

import { ThemeToggle } from '@/components/ui/ThemeToggle'

import { findNavItem } from './navigation'

export function Topbar({ onOpenMenu }: { onOpenMenu: () => void }) {
  const current = findNavItem(useLocation().pathname)
  const today = new Date().toLocaleDateString('vi-VN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })

  return (
    <header className="sticky top-0 z-20 flex h-16 shrink-0 items-center gap-3 border-b border-line bg-surface/80 px-4 backdrop-blur-md md:px-8">
      <button onClick={onOpenMenu} className="btn-ghost h-10 w-10 p-0 lg:hidden" aria-label="Mở menu">
        <Menu size={20} />
      </button>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold">{current?.label}</p>
        <p className="hidden truncate text-xs text-muted capitalize sm:block">{today}</p>
      </div>
      <ThemeToggle />
    </header>
  )
}
