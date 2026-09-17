import { Eye, EyeOff, Loader2 } from 'lucide-react'
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
    <div className="relative flex min-h-dvh flex-col items-center justify-center bg-surface-2 px-4">
      <ThemeToggle className="btn-ghost absolute top-4 right-4 h-8 w-8 px-0" />

      <div className="w-full max-w-[360px]">
        <div className="mb-8 flex flex-col items-center text-center">
          <img src="/logo.png" alt="HaUI" className="mb-4 h-11 w-11 rounded-xl bg-white object-contain p-1 shadow-sm ring-1 ring-line" />
          <h1 className="text-xl font-semibold">Đăng nhập cổng sinh viên</h1>
          <p className="mt-1 text-muted">Trường Đại học Công nghiệp Hà Nội</p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-4 p-6">
          <label className="block space-y-1.5">
            <span className="text-[13px] font-medium">Tên đăng nhập</span>
            <input name="username" required autoComplete="username" autoFocus placeholder="SV001_tk" className="input" />
          </label>

          <label className="block space-y-1.5">
            <span className="text-[13px] font-medium">Mật khẩu</span>
            <div className="relative">
              <input name="password" type={showPassword ? 'text' : 'password'} required autoComplete="current-password" className="input pr-9" />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute top-1/2 right-1 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-md text-muted hover:text-fg"
                aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
              >
                {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </label>

          {error && <p className="text-[13px] text-danger">{error}</p>}

          <button type="submit" disabled={submitting} className="btn-primary w-full">
            {submitting && <Loader2 size={15} className="animate-spin" />}
            Đăng nhập
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-muted">Quên mật khẩu? Liên hệ phòng Đào tạo để được cấp lại.</p>
      </div>
    </div>
  )
}
