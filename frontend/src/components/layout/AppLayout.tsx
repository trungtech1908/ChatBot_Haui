import { Menu } from 'lucide-react'
import { useState } from 'react'
import { Outlet, useLocation } from 'react-router'

import { cn } from '@/lib/cn'

import { findNavItem } from './navigation'
import { Sidebar } from './Sidebar'

export function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(false)
  const { pathname } = useLocation()

  return (
    <div className="flex h-dvh bg-bg">
      <aside className="hidden w-64 shrink-0 lg:block">
        <Sidebar />
      </aside>

      {/* Menu ngăn kéo trên màn hình nhỏ */}
      <div
        className={cn('fixed inset-0 z-30 bg-black/40 transition-opacity lg:hidden', menuOpen ? 'opacity-100' : 'pointer-events-none opacity-0')}
        onClick={() => setMenuOpen(false)}
      />
      <aside className={cn('fixed inset-y-0 left-0 z-40 w-64 transition-transform duration-200 lg:hidden', menuOpen ? 'translate-x-0' : '-translate-x-full')}>
        <Sidebar onNavigate={() => setMenuOpen(false)} />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center gap-2 border-b border-line bg-surface px-3 lg:hidden">
          <button onClick={() => setMenuOpen(true)} className="btn-ghost h-9 w-9 px-0" aria-label="Mở menu">
            <Menu size={18} />
          </button>
          <span className="font-semibold">{findNavItem(pathname)?.label}</span>
        </header>
        <main className="min-h-0 flex-1 overflow-y-auto">
          <div className="mx-auto max-w-7xl px-4 py-6 md:px-8 md:py-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
