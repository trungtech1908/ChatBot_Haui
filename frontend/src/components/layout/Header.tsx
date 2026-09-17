import { Menu } from 'lucide-react'

import { useProfile } from '@/api/students'
import { ThemeToggle } from '@/components/ui/ThemeToggle'
import { useAuth } from '@/features/auth/useAuth'

export function Header({ onOpenMenu }: { onOpenMenu: () => void }) {
  const { logout } = useAuth()
  const { data: profile } = useProfile()

  return (
    <header className="flex h-14 shrink-0 items-center gap-3 bg-[#0e3a6b] px-3 text-white md:px-5 dark:bg-[#0b213b]">
      <button onClick={onOpenMenu} className="rounded p-1.5 hover:bg-white/10 lg:hidden" aria-label="Mở menu">
        <Menu size={20} />
      </button>
      <img src="/logo.png" alt="" className="hidden h-9 w-9 rounded-sm bg-white object-contain p-0.5 sm:block" />
      <div className="min-w-0 flex-1 leading-tight">
        <p className="hidden truncate text-[11px] tracking-wide text-white/70 uppercase sm:block">Trường Đại học Công nghiệp Hà Nội</p>
        <p className="truncate text-sm font-semibold">Cổng thông tin sinh viên</p>
      </div>
      {profile && (
        <div className="hidden text-right leading-tight sm:block">
          <p className="text-sm font-medium">{profile.fullName}</p>
          <p className="text-xs text-white/70">{profile.studentId}</p>
        </div>
      )}
      <ThemeToggle className="rounded p-2 hover:bg-white/10" />
      <button onClick={logout} className="shrink-0 rounded border border-white/30 px-2.5 py-1 text-sm hover:bg-white/10">
        Đăng xuất
      </button>
    </header>
  )
}
