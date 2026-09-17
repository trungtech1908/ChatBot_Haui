import { LogOut } from 'lucide-react'
import { NavLink } from 'react-router'

import { useProfile } from '@/api/students'
import { Avatar } from '@/components/ui/Avatar'
import { useAuth } from '@/features/auth/useAuth'
import { cn } from '@/lib/cn'

import { assistantItem, navigation } from './navigation'

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const { logout } = useAuth()
  const { data: profile } = useProfile()
  const AssistantIcon = assistantItem.icon

  return (
    <div className="flex h-full flex-col border-r border-line bg-surface">
      <div className="flex h-16 items-center gap-3 px-5">
        <img src="/logo.png" alt="HaUI" className="h-9 w-9 rounded-lg bg-white object-contain p-1 ring-1 ring-line" />
        <div className="leading-tight">
          <p className="text-sm font-bold">HaUI Student</p>
          <p className="text-xs text-muted">Cổng thông tin sinh viên</p>
        </div>
      </div>

      <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-4">
        <NavLink
          to={assistantItem.to}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-white shadow-md shadow-indigo-500/25 transition',
              'bg-gradient-to-r from-blue-600 to-indigo-600 hover:brightness-110',
              isActive && 'ring-2 ring-indigo-300 ring-offset-2 ring-offset-surface dark:ring-indigo-500',
            )
          }
        >
          <AssistantIcon size={18} /> {assistantItem.label}
        </NavLink>

        {navigation.map((section) => (
          <div key={section.title}>
            <p className="mb-2 px-3 text-[11px] font-semibold tracking-wider text-muted uppercase">{section.title}</p>
            <div className="space-y-0.5">
              {section.items.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  end
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    cn(
                      'group flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition',
                      isActive ? 'bg-primary-soft text-primary' : 'text-muted hover:bg-surface-2 hover:text-fg',
                    )
                  }
                >
                  <Icon size={18} className="shrink-0" />
                  {label}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-line p-3">
        <div className="flex items-center gap-3 rounded-xl p-2">
          <Avatar name={profile?.fullName} />
          <div className="min-w-0 flex-1 leading-tight">
            <p className="truncate text-sm font-semibold">{profile?.fullName ?? '...'}</p>
            <p className="truncate text-xs text-muted">{profile?.studentId}</p>
          </div>
          <button onClick={logout} className="btn-ghost h-9 w-9 p-0" title="Đăng xuất" aria-label="Đăng xuất">
            <LogOut size={17} />
          </button>
        </div>
      </div>
    </div>
  )
}
