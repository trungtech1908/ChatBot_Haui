import { NavLink } from 'react-router'

import { cn } from '@/lib/cn'

import { navigation } from './navigation'

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="h-full overflow-y-auto border-r border-line bg-surface py-3">
      {navigation.map((section) => (
        <div key={section.title} className="mb-3">
          <p className="px-5 py-1.5 text-[11px] font-semibold tracking-wider text-muted uppercase">{section.title}</p>
          {section.items.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end
              onClick={onNavigate}
              className={({ isActive }) =>
                cn(
                  'block border-l-[3px] px-[17px] py-1.5 text-sm',
                  isActive ? 'border-brand bg-brand-soft font-medium text-brand' : 'border-transparent text-fg hover:bg-surface-2',
                )
              }
            >
              {label}
            </NavLink>
          ))}
        </div>
      ))}
    </nav>
  )
}
