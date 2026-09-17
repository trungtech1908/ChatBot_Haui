import { NavLink } from 'react-router'

import { navigation } from './navigation'

export function Sidebar({ open, onNavigate }: { open: boolean; onNavigate: () => void }) {
  return (
    <nav
      className={`${open ? 'translate-x-0' : '-translate-x-full'} fixed top-16 bottom-0 left-0 z-30 w-64 overflow-y-auto bg-blue-900 text-white shadow-xl transition-transform md:static md:translate-x-0`}
    >
      <div className="border-b border-blue-700 bg-blue-800 p-4 text-center font-bold tracking-wider uppercase">
        Menu chức năng
      </div>
      <div className="space-y-1 p-2">
        {navigation.map((section, i) => (
          <div key={i} className={i > 0 ? 'mt-2 border-t border-blue-800 pt-2' : ''}>
            {section.title && <div className="px-3 py-1 text-xs font-bold text-blue-400 uppercase">{section.title}</div>}
            {section.items.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                onClick={onNavigate}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded border-l-4 p-3 text-sm transition-colors hover:bg-blue-700 ${
                    isActive ? 'border-yellow-400 bg-blue-800 font-bold text-white shadow-md' : 'border-transparent text-blue-100'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon size={18} className={isActive ? 'text-yellow-300' : ''} />
                    {label}
                  </>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </div>
    </nav>
  )
}
