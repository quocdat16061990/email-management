import { Link, useLocation } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import { useLogout } from '../../hooks/useAuth'
import { cn } from '../../lib/utils'

const navItems = [
  { path: '/dashboard', label: 'Khách Telegram' },
  { path: '/chatgpt-accounts', label: 'Tài khoản ChatGPT' },
]

export default function Header() {
  const location = useLocation()
  const logoutMutation = useLogout()

  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/dashboard" className="flex items-center gap-3">
            <img src="/logo.png" alt="Logo" className="w-9 h-9 object-contain" />
            <span className="text-lg font-bold text-gray-900 hidden sm:block">Anh Lập Trình</span>
          </Link>

          <nav className="flex items-center gap-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  'px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  location.pathname.startsWith(item.path)
                    ? 'bg-brand-50 text-brand-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100',
                )}
              >
                {item.label}
              </Link>
            ))}
            <div className="w-px h-6 bg-gray-200 mx-2" />
            <button
              onClick={() => logoutMutation.mutate()}
              disabled={logoutMutation.isPending}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:text-red-600 hover:bg-red-50 transition-colors"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">{logoutMutation.isPending ? 'Đang đăng xuất...' : 'Đăng xuất'}</span>
            </button>
          </nav>
        </div>
      </div>
    </header>
  )
}
