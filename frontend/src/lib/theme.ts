import { useCallback, useSyncExternalStore } from 'react'

type Theme = 'light' | 'dark'
const KEY = 'theme'
const listeners = new Set<() => void>()
// Theme ban đầu do script trong index.html đặt trước khi render

function apply(theme: Theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark')
}

const getTheme = (): Theme => (document.documentElement.classList.contains('dark') ? 'dark' : 'light')

export function useTheme() {
  const theme = useSyncExternalStore((cb) => {
    listeners.add(cb)
    return () => listeners.delete(cb)
  }, getTheme)

  const toggle = useCallback(() => {
    const next: Theme = getTheme() === 'dark' ? 'light' : 'dark'
    apply(next)
    try {
      localStorage.setItem(KEY, next)
    } catch {
      // Không lưu được thì chỉ áp dụng cho phiên hiện tại
    }
    listeners.forEach((cb) => cb())
  }, [])

  return { theme, toggle }
}
