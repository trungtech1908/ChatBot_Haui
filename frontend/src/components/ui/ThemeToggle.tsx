import { Moon, Sun } from 'lucide-react'

import { useTheme } from '@/lib/theme'

export function ThemeToggle() {
  const { theme, toggle } = useTheme()
  const dark = theme === 'dark'
  return (
    <button onClick={toggle} className="btn-ghost h-10 w-10 p-0" title={dark ? 'Giao diện sáng' : 'Giao diện tối'} aria-label="Đổi giao diện">
      {dark ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  )
}
