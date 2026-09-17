import { useState } from 'react'
import { Outlet, useLocation } from 'react-router'

import { cn } from '@/lib/cn'

import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'

// Trang chiếm trọn chiều cao, không padding (chat)
const FULL_BLEED = new Set(['/chat'])

export function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(false)
  const { pathname } = useLocation()
  const fullBleed = FULL_BLEED.has(pathname)

  return (
    <div className="flex h-dvh overflow-hidden">
      <aside className="hidden w-64 shrink-0 lg:block">
        <Sidebar />
      </aside>

      {/* Drawer trên mobile */}
      <div className={cn('fixed inset-0 z-40 lg:hidden', !menuOpen && 'pointer-events-none')}>
        <div
          onClick={() => setMenuOpen(false)}
          className={cn('absolute inset-0 bg-slate-950/40 backdrop-blur-sm transition-opacity', menuOpen ? 'opacity-100' : 'opacity-0')}
        />
        <aside className={cn('absolute inset-y-0 left-0 w-72 shadow-2xl transition-transform duration-300', menuOpen ? 'translate-x-0' : '-translate-x-full')}>
          <Sidebar onNavigate={() => setMenuOpen(false)} />
        </aside>
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onOpenMenu={() => setMenuOpen(true)} />
        <main className={cn('flex-1', fullBleed ? 'overflow-hidden' : 'overflow-y-auto')}>
          {fullBleed ? (
            <Outlet />
          ) : (
            <div key={pathname} className="mx-auto w-full max-w-7xl animate-fade-up p-4 md:p-8">
              <Outlet />
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
