import { useState } from 'react'
import { Outlet } from 'react-router'

import { cn } from '@/lib/cn'

import { Header } from './Header'
import { Sidebar } from './Sidebar'

export function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="flex h-dvh flex-col">
      <Header onOpenMenu={() => setMenuOpen(true)} />
      <div className="relative flex min-h-0 flex-1">
        <aside className="hidden w-60 shrink-0 lg:block">
          <Sidebar />
        </aside>

        {/* Menu dạng ngăn kéo trên màn hình nhỏ */}
        {menuOpen && <div className="absolute inset-0 z-30 bg-black/30 lg:hidden" onClick={() => setMenuOpen(false)} />}
        <aside className={cn('absolute inset-y-0 left-0 z-40 w-64 shadow-lg lg:hidden', !menuOpen && 'hidden')}>
          <Sidebar onNavigate={() => setMenuOpen(false)} />
        </aside>

        <main className="min-w-0 flex-1 overflow-y-auto">
          <div className="mx-auto max-w-6xl px-4 py-5 md:px-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
