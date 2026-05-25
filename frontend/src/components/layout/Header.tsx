import { Link, useLocation } from 'react-router-dom'
import { useLogout } from '../../hooks/useAuth'
import { cn } from '../../lib/utils'

const navItems = [
  { path: '/dashboard', label: 'Học viên' },
  { path: '/courses', label: 'Khóa học' },
]

export default function Header() {
  const location = useLocation()
  const logoutMutation = useLogout()

  return (
    <header className="sticky top-0 z-50 bg-white/70 backdrop-blur-xl border-b border-gray-200/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <Link to="/dashboard" className="flex items-center gap-3">
            <img 
              src="/logo.png" 
              alt="Logo" 
              className="w-9 h-9 object-contain" 
            />
            <span className="text-lg font-bold bg-gradient-to-r from-brand-600 via-accent-500 to-rose-500 bg-clip-text text-transparent hidden sm:block">
              Anh Lap Trinh
            </span>
          </Link>

          {/* Nav */}
          <nav className="flex items-center gap-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                  location.pathname.startsWith(item.path)
                    ? 'bg-brand-50 text-brand-700 shadow-sm'
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
              className="px-4 py-2 rounded-lg text-sm font-medium text-gray-600 hover:text-red-600 hover:bg-red-50 transition-all duration-200"
            >
              {logoutMutation.isPending ? 'Đang đăng xuất...' : 'Đăng xuất'}
            </button>
          </nav>
        </div>
      </div>
    </header>
  )
}
