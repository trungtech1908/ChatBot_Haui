import { createContext, use } from 'react'

export interface AuthContextValue {
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth() {
  const context = use(AuthContext)
  if (!context) throw new Error('useAuth phải dùng bên trong AuthProvider')
  return context
}
