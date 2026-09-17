import { BookOpenCheck, Eye, EyeOff, Loader2, Lock, MessagesSquare, ShieldCheck, User, Wallet } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router'

import { ThemeToggle } from '@/components/ui/ThemeToggle'

import { useAuth } from './useAuth'

const features = [
  { icon: BookOpenCheck, title: 'Theo dõi học tập', text: 'Điểm số, lịch học, lịch thi và tiến độ tốt nghiệp ở một nơi.' },
  { icon: Wallet, title: 'Quản lý tài chính', text: 'Số dư, công nợ, học bổng và lịch sử giao dịch rõ ràng.' },
  { icon: MessagesSquare, title: 'Trợ lý AI', text: 'Hỏi đáp quy chế, học phí, học bổng của trường 24/7.' },
]

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
    <div className="grid min-h-dvh lg:grid-cols-2">
      <div className="relative hidden overflow-hidden bg-gradient-to-br from-blue-700 via-indigo-700 to-violet-800 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="pointer-events-none absolute -top-32 -right-32 h-96 w-96 rounded-full bg-white/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-40 -left-20 h-[28rem] w-[28rem] rounded-full bg-sky-400/20 blur-3xl" />

        <div className="relative flex items-center gap-3">
          <img src="/logo.png" alt="HaUI" className="h-11 w-11 rounded-xl bg-white object-contain p-1.5" />
          <div className="leading-tight">
            <p className="font-bold">HaUI Student</p>
            <p className="text-sm text-blue-100">Đại học Công nghiệp Hà Nội</p>
          </div>
        </div>

        <div className="relative max-w-md">
          <h1 className="text-4xl leading-tight font-bold tracking-tight">Mọi thông tin học tập, trong một cổng duy nhất.</h1>
          <div className="mt-10 space-y-6">
            {features.map(({ icon: Icon, title, text }) => (
              <div key={title} className="flex gap-4">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/15 ring-1 ring-white/20">
                  <Icon size={20} />
                </span>
                <div>
                  <p className="font-semibold">{title}</p>
                  <p className="text-sm text-blue-100">{text}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <p className="relative text-sm text-blue-200">© {new Date().getFullYear()} Hệ thống Quản lý Sinh viên HaUI</p>
      </div>

      <div className="relative flex items-center justify-center bg-bg p-6">
        <div className="absolute top-4 right-4">
          <ThemeToggle />
        </div>

        <form onSubmit={handleSubmit} className="w-full max-w-sm animate-fade-up">
          <img src="/logo.png" alt="HaUI" className="mb-6 h-14 w-14 rounded-2xl bg-white object-contain p-2 shadow-sm ring-1 ring-line lg:hidden" />
          <h2 className="text-2xl font-bold tracking-tight">Chào mừng trở lại 👋</h2>
          <p className="mt-1 text-sm text-muted">Đăng nhập bằng tài khoản sinh viên của bạn.</p>

          {error && (
            <div className="mt-6 flex items-center gap-2 rounded-xl border border-rose-500/25 bg-rose-500/5 px-3.5 py-2.5 text-sm text-rose-700 dark:text-rose-400">
              <ShieldCheck size={16} /> {error}
            </div>
          )}

          <div className="mt-6 space-y-4">
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium">Tên đăng nhập</span>
              <div className="relative">
                <User size={16} className="pointer-events-none absolute top-1/2 left-3.5 -translate-y-1/2 text-muted" />
                <input name="username" required autoComplete="username" placeholder="VD: SV001_tk" className="input pl-10" />
              </div>
            </label>
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium">Mật khẩu</span>
              <div className="relative">
                <Lock size={16} className="pointer-events-none absolute top-1/2 left-3.5 -translate-y-1/2 text-muted" />
                <input
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className="input px-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute top-1/2 right-2 -translate-y-1/2 rounded-lg p-1.5 text-muted hover:text-fg"
                  aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </label>
          </div>

          <button type="submit" disabled={submitting} className="btn-primary mt-6 w-full py-3">
            {submitting && <Loader2 size={16} className="animate-spin" />}
            {submitting ? 'Đang đăng nhập...' : 'Đăng nhập'}
          </button>
        </form>
      </div>
    </div>
  )
}
