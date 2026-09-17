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
    <div className="flex h-full flex-col">
      <div className="flex h-14 items-center gap-2.5 px-4">
        <img src="/logo.png" alt="" className="h-7 w-7 rounded-md bg-white object-contain p-0.5 ring-1 ring-line" />
        <div className="leading-tight">
          <p className="text-[13px] font-semibold">HaUI</p>
          <p className="text-xs text-muted">Cổng sinh viên</p>
        </div>
      </div>

      <nav className="flex-1 space-y-5 overflow-y-auto px-2.5 py-2">
        {navigation.map((section, i) => (
          <div key={i}>
            {section.title && <p className="mb-1 px-2.5 text-xs font-medium text-muted">{section.title}</p>}
            <div className="space-y-px">
              {section.items.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  end
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    cn(
                      'flex h-8 items-center gap-2.5 rounded-lg px-2.5 text-[13px] transition-colors',
                      isActive
                        ? 'bg-surface font-medium text-fg shadow-[0_1px_2px_rgb(0_0_0/0.06)] ring-1 ring-line'
                        : 'text-muted hover:bg-hover hover:text-fg',
                    )
                  }
                >
                  <Icon size={16} strokeWidth={1.75} className="shrink-0" />
                  {label}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="flex items-center gap-2 border-t border-line px-3 py-3">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-hover text-xs font-semibold ring-1 ring-line">
          {initials(profile?.fullName)}
        </span>
        <div className="min-w-0 flex-1 leading-tight">
          <p className="truncate text-[13px] font-medium">{profile?.fullName}</p>
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
