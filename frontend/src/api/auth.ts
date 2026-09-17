import { apiJson } from '@/lib/api'

export const login = (username: string, password: string) =>
  apiJson<{ access_token: string }>('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) })
