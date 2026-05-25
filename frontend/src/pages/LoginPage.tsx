import { useAuth } from '../context/AuthContext'
import { useLogin } from '../hooks/useAuth'
import { Navigate } from 'react-router-dom'
import { showToast } from '../components/shared/Toast'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const loginSchema = z.object({
  email: z.string()
    .trim()
    .min(1, 'Email không được để trống')
    .email('Email không hợp lệ'),
  password: z.string().min(1, 'Mật khẩu không được để trống'),
})

type LoginFormValues = z.infer<typeof loginSchema>

export default function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth()
  const loginMutation = useLogin()

  const { register, handleSubmit, formState: { errors } } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-10 h-10 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (isAuthenticated) return <Navigate to="/dashboard" replace />

  const onSubmit = (data: LoginFormValues) => {
    loginMutation.mutate(
      { email: data.email, password: data.password },
      {
        onError: (err: Error) => {
          showToast('error', err.message || 'Đăng nhập thất bại')
        },
      },
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f8fafc] px-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl shadow-gray-200/50 border border-gray-100 p-8">
          {/* Logo */}
          <div className="flex flex-col items-center mb-8">
            <img 
              src="/logo.png" 
              alt="Logo" 
              className="w-16 h-16 object-contain mb-4" 
            />
            <h1 className="text-xl font-bold text-gray-900">Anh Lap Trinh</h1>
            <p className="text-sm text-gray-500 mt-1">Đăng nhập để quản lý hệ thống</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Email</label>
              <input
                type="email"
                placeholder="admin@example.com"
                {...register('email')}
                className={`w-full px-4 py-2.5 rounded-xl border text-sm transition-all focus:outline-none focus:ring-2 focus:ring-brand-500/20 ${
                  errors.email ? 'border-red-300 focus:border-red-300' : 'border-gray-200 focus:border-brand-300'
                }`}
              />
              {errors.email && <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Mật khẩu</label>
              <input
                type="password"
                placeholder="••••••••"
                {...register('password')}
                className={`w-full px-4 py-2.5 rounded-xl border text-sm transition-all focus:outline-none focus:ring-2 focus:ring-brand-500/20 ${
                  errors.password ? 'border-red-300 focus:border-red-300' : 'border-gray-200 focus:border-brand-300'
                }`}
              />
              {errors.password && <p className="mt-1 text-xs text-red-500">{errors.password.message}</p>}
            </div>

            <button
              type="submit"
              disabled={loginMutation.isPending}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-brand-500 to-accent-600 text-white text-sm font-semibold shadow-lg shadow-brand-500/25 hover:shadow-xl hover:shadow-brand-500/30 hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loginMutation.isPending ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Đang đăng nhập...
                </span>
              ) : (
                'Đăng nhập vào hệ thống'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
