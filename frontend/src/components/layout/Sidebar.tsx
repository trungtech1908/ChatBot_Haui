import { LogOut } from 'lucide-react'
import { NavLink } from 'react-router'

import { useProfile } from '@/api/students'
import { ThemeToggle } from '@/components/ui/ThemeToggle'
import { useAuth } from '@/features/auth/useAuth'
import { cn } from '@/lib/cn'

import { navigation } from './navigation'

const initials = (name?: string | null) => (name ?? '').trim().split(/\s+/).slice(-2).map((w) => w[0]).join('').toUpperCase()

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const { logout } = useAuth()
  const { data: profile } = useProfile()

  return (
    <div className="flex h-full flex-col border-r border-line bg-surface">
      <div className="flex h-16 items-center gap-3 border-b border-line px-5">
        <img src="/logo.png" alt="" className="h-9 w-9 rounded-lg bg-white object-contain p-0.5 ring-1 ring-line" />
        <div className="leading-tight">
          <p className="font-semibold">HaUI</p>
          <p className="text-xs text-muted">Cổng thông tin sinh viên</p>
        </div>
      </div>

      <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-4" aria-label="Điều hướng chính">
        {navigation.map((section, i) => (
          <div key={i}>
            {section.title && <p className="mb-1.5 px-3 text-[11px] font-semibold tracking-wider text-muted uppercase">{section.title}</p>}
            <div className="space-y-0.5">
              {section.items.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  end
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    cn(
                      'group flex h-9 items-center gap-3 rounded-lg px-3 text-[13px] font-medium transition-colors',
                      isActive ? 'bg-brand-soft text-brand-ink' : 'text-fg-2 hover:bg-hover hover:text-fg',
                    )
                  }
                >
                  {({ isActive }) => (
                    <>
                      <Icon size={17} strokeWidth={1.9} className={cn('shrink-0', isActive ? 'text-brand' : 'text-muted group-hover:text-fg-2')} />
                      {label}
                    </>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="flex items-center gap-2.5 border-t border-line p-3">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand text-xs font-semibold text-white">
          {initials(profile?.fullName)}
        </span>
        <div className="min-w-0 flex-1 leading-tight">
          <p className="truncate text-[13px] font-semibold">{profile?.fullName}</p>
          <p className="truncate text-xs text-muted">{profile?.studentId}</p>
        </div>
        <ThemeToggle className="btn-ghost h-8 w-8 px-0" />
        <button onClick={logout} className="btn-ghost h-8 w-8 px-0" title="Đăng xuất" aria-label="Đăng xuất">
          <LogOut size={15} />
        </button>
      </div>
    </div>
  )
}
