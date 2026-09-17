import { LogIn } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router'

import { useAuth } from './useAuth'

export function LoginPage() {
  const { isAuthenticated, login } = useAuth()
  const navigate = useNavigate()
  const from = (useLocation().state as { from?: string } | null)?.from ?? '/'
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (isAuthenticated) return <Navigate to={from} replace />

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    setSubmitting(true)
    setError(null)
    try {
      await login(String(form.get('username')), String(form.get('password')))
      navigate(from, { replace: true })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Đăng nhập thất bại')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-800 to-blue-950 p-4">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-5 rounded-2xl bg-white p-8 shadow-xl">
        <div className="text-center">
          <img src="/logo.png" alt="HaUI" className="mx-auto mb-3 h-16 object-contain" />
          <h1 className="text-xl font-bold text-gray-800">Đăng nhập</h1>
          <p className="text-sm text-gray-500">Hệ thống Quản lý Sinh viên</p>
        </div>

        {error && <p className="rounded-lg bg-red-50 p-3 text-center text-sm text-red-600">{error}</p>}

        <label className="block space-y-1">
          <span className="text-sm font-medium text-gray-700">Tên đăng nhập</span>
          <input name="username" required autoComplete="username" className="input" />
        </label>
        <label className="block space-y-1">
          <span className="text-sm font-medium text-gray-700">Mật khẩu</span>
          <input name="password" type="password" required autoComplete="current-password" className="input" />
        </label>

        <button
          type="submit"
          disabled={submitting}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-700 py-2.5 font-semibold text-white transition hover:bg-blue-800 disabled:opacity-60"
        >
          <LogIn size={18} /> {submitting ? 'Đang đăng nhập...' : 'Đăng nhập'}
        </button>
      </form>
    </div>
  )
}
