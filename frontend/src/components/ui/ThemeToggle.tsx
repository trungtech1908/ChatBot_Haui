import { Moon, Sun } from 'lucide-react'

import { useTheme } from '@/lib/theme'

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, toggle } = useTheme()
  const dark = theme === 'dark'
  return (
    <button onClick={toggle} className={className} title={dark ? 'Giao diện sáng' : 'Giao diện tối'} aria-label="Đổi giao diện">
      {dark ? <Sun size={16} /> : <Moon size={16} />}
    </button>
  )
}
