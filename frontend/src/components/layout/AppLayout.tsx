import { useState } from 'react'
import { Outlet } from 'react-router'

import { Header } from './Header'
import { Sidebar } from './Sidebar'

export function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="flex h-screen flex-col bg-gray-100">
      <Header onToggleMenu={() => setMenuOpen((open) => !open)} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar open={menuOpen} onNavigate={() => setMenuOpen(false)} />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
