import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { login as loginRequest } from '@/api/auth'
import { setUnauthorizedHandler, tokenStorage } from '@/lib/api'

import { AuthContext } from './useAuth'

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [token, setToken] = useState(tokenStorage.get)

  const login = useCallback(async (username: string, password: string) => {
    const { access_token } = await loginRequest(username, password)
    tokenStorage.set(access_token)
    setToken(access_token)
  }, [])

  const logout = useCallback(() => {
    tokenStorage.clear()
    setToken(null)
    queryClient.clear()
  }, [queryClient])

  useEffect(() => setUnauthorizedHandler(logout), [logout])

  const value = useMemo(() => ({ isAuthenticated: !!token, login, logout }), [token, login, logout])
  return <AuthContext value={value}>{children}</AuthContext>
}
