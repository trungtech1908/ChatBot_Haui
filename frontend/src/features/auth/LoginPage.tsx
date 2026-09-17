import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router'

import { ThemeToggle } from '@/components/ui/ThemeToggle'

import { useAuth } from './useAuth'

export function LoginPage() {
  const { isAuthenticated, login } = useAuth()
  const navigate = useNavigate()
  const from = (useLocation().state as { from?: string } | null)?.from ?? '/'
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

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
    <div className="flex min-h-dvh flex-col">
      <header className="flex h-14 items-center gap-3 bg-[#0e3a6b] px-4 text-white md:px-6 dark:bg-[#0b213b]">
        <img src="/logo.png" alt="" className="h-9 w-9 rounded-sm bg-white object-contain p-0.5" />
        <div className="flex-1 leading-tight">
          <p className="text-[11px] tracking-wide text-white/70 uppercase">Trường Đại học Công nghiệp Hà Nội</p>
          <p className="text-sm font-semibold">Cổng thông tin sinh viên</p>
        </div>
        <ThemeToggle className="rounded p-2 hover:bg-white/10" />
      </header>

      <main className="flex flex-1 items-start justify-center px-4 pt-16 pb-10">
        <div className="w-full max-w-sm">
          <form onSubmit={handleSubmit} className="rounded-md border border-line bg-surface">
            <div className="border-b border-line px-5 py-3">
              <h1 className="font-semibold">Đăng nhập</h1>
              <p className="text-sm text-muted">Dùng tài khoản sinh viên do nhà trường cấp.</p>
            </div>

            <div className="space-y-4 px-5 py-4">
              {error && <p className="border-l-2 border-accent pl-2 text-sm text-accent">{error}</p>}

              <label className="block">
                <span className="mb-1 block text-sm">Tên đăng nhập</span>
                <input name="username" required autoComplete="username" autoFocus className="input" />
              </label>

              <label className="block">
                <span className="mb-1 flex items-center justify-between text-sm">
                  Mật khẩu
                  <button type="button" onClick={() => setShowPassword((v) => !v)} className="text-xs link">
                    {showPassword ? 'Ẩn' : 'Hiện'}
                  </button>
                </span>
                <input name="password" type={showPassword ? 'text' : 'password'} required autoComplete="current-password" className="input" />
              </label>

              <button type="submit" disabled={submitting} className="btn-primary w-full">
                {submitting ? 'Đang đăng nhập…' : 'Đăng nhập'}
              </button>
            </div>
          </form>
          <p className="mt-4 text-center text-xs text-muted">Quên mật khẩu? Liên hệ phòng Đào tạo để được cấp lại.</p>
        </div>
      </main>
    </div>
  )
}
