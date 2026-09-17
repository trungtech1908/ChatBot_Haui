import { LogOut, Menu } from 'lucide-react'

import { useProfile } from '@/api/students'
import { useAuth } from '@/features/auth/useAuth'

export function Header({ onToggleMenu }: { onToggleMenu: () => void }) {
  const { logout } = useAuth()
  const { data: profile } = useProfile()

  return (
    <header className="z-40 flex h-16 flex-shrink-0 items-center justify-between bg-blue-800 px-4 text-white shadow-md md:px-6">
      <div className="flex items-center gap-3">
        <button onClick={onToggleMenu} className="rounded p-1 hover:bg-blue-700 md:hidden" aria-label="Mở menu">
          <Menu />
        </button>
        <h1 className="text-sm font-bold tracking-wide uppercase sm:text-base md:text-xl">Hệ thống Quản lý Sinh viên</h1>
      </div>
      <div className="flex items-center gap-4 text-sm">
        <span className="hidden sm:inline">
          Xin chào, <span className="font-bold text-yellow-300">{profile?.fullName ?? profile?.username}</span>
        </span>
        <button
          onClick={logout}
          title="Đăng xuất"
          className="flex items-center gap-2 rounded bg-red-500 px-3 py-1.5 shadow transition hover:bg-red-600"
        >
          <LogOut size={16} /> <span className="hidden sm:inline">Đăng xuất</span>
        </button>
      </div>
    </header>
  )
}
