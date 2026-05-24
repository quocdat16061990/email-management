import { useParams, Link } from 'react-router-dom'
import { useStudentDetail } from '../hooks/useStudents'
import Avatar from '../components/shared/Avatar'
import StatusBadge from '../components/shared/StatusBadge'
import LoadingSpinner from '../components/shared/LoadingSpinner'
import ErrorState from '../components/shared/ErrorState'

function ExpiryProgress({ regDate, expDate }: { regDate?: string | null; expDate?: string | null }) {
  if (!regDate || !expDate) {
    return <p className="text-sm text-gray-400 italic">Chưa thiết lập</p>
  }

  const now = new Date()
  const start = new Date(regDate)
  const end = new Date(expDate)
  const total = end.getTime() - start.getTime()
  const passed = now.getTime() - start.getTime()

  if (total <= 0) return <p className="text-sm text-gray-400 italic">Không xác định</p>

  const percent = Math.round((passed / total) * 100)
  const remainingDays = Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))

  const getColor = (pct: number) => {
    if (pct >= 90) return 'bg-red-500'
    if (pct >= 75) return 'bg-amber-500'
    return 'bg-emerald-500'
  }

  const clampedPct = Math.min(100, Math.max(0, percent))

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-gray-500">
        <span>{remainingDays > 0 ? `Còn lại ${remainingDays} ngày` : remainingDays === 0 ? 'Hết hạn hôm nay!' : `Đã quá hạn ${Math.abs(remainingDays)} ngày`}</span>
        <span className="font-medium">{Math.min(clampedPct, 100)}%</span>
      </div>
      <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-500 ${getColor(clampedPct)}`} style={{ width: `${Math.min(clampedPct, 100)}%` }} />
      </div>
    </div>
  )
}

export default function StudentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: student, isLoading, isError, refetch } = useStudentDetail(id ? parseInt(id) : null)

  if (isLoading) return <LoadingSpinner />
  if (isError) return <ErrorState onRetry={() => refetch()} />
  if (!student) return <ErrorState message="Không tìm thấy học viên." />

  return (
    <div className="space-y-6">
      {/* Back */}
      <Link to="/dashboard" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-brand-600 transition-colors">
        <svg className="w-4 h-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/></svg>
        Quay lại Bảng điều khiển
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="p-6 text-center">
              <Avatar name={student.full_name} size="lg" />
              <h2 className="mt-3 text-lg font-bold text-gray-900">{student.full_name || 'Chưa cập nhật'}</h2>
              <div className="mt-2"><StatusBadge status={student.status} /></div>
            </div>
            <div className="px-6 pb-6 space-y-4">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Email</p>
                <p className="text-sm text-gray-900">{student.customer_email}</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Số điện thoại</p>
                <p className="text-sm text-gray-900">{student.phone_number || 'Chưa cập nhật'}</p>
              </div>
              {student.telegram_chat_id && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Telegram Chat ID</p>
                  <p className="text-sm text-gray-900 flex items-center gap-1.5 mt-0.5">
                    {student.telegram_chat_id}
                    {student.is_verified_telegram ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-100">
                        Đã xác thực
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-100">
                        Chưa xác thực
                      </span>
                    )}
                  </p>
                </div>
              )}
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Tổng quan thời gian</p>
                <ExpiryProgress regDate={student.registration_date} expDate={student.expiry_date} />
              </div>
            </div>
          </div>
        </div>

        {/* Enrollments */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-lg font-bold text-gray-900">Khóa học đã đăng ký</h3>
          {(!student.enrollments || student.enrollments.length === 0) ? (
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-8 text-center">
              <p className="text-sm text-gray-400 italic">Học viên chưa đăng ký khóa học nào.</p>
            </div>
          ) : (
            student.enrollments.map((e: any) => (
              <div key={e.course_id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <Link to={`/courses/${e.course_id}`} className="font-semibold text-gray-900 hover:text-brand-600">
                      {e.course_name}
                    </Link>
                    {e.course_description && <p className="text-sm text-gray-500 mt-0.5">{e.course_description}</p>}
                  </div>
                  <StatusBadge status={e.status} />
                </div>
                <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
                  <div>
                    <span className="text-gray-500">Đăng ký:</span>{' '}
                    <span className="font-medium text-gray-700">{e.registration_date || '-'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Hết hạn:</span>{' '}
                    <span className="font-medium text-gray-700">{e.expiry_date || '-'}</span>
                  </div>
                </div>
                <ExpiryProgress regDate={e.registration_date} expDate={e.expiry_date} />
                {/* Links */}
                {(e.web_link || (e.links && e.links.length > 0)) && (
                  <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-gray-100">
                    {e.web_link && (
                      <a href={e.web_link} target="_blank" rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-brand-50 text-brand-700 text-xs font-medium hover:bg-brand-100 transition-colors">
                        <svg className="w-3.5 h-3.5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                        Website Khóa Học
                      </a>
                    )}
                    {(e.links || []).map((link: any, i: number) => (
                      <a key={i} href={link.url} target="_blank" rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-purple-50 text-purple-700 text-xs font-medium hover:bg-purple-100 transition-colors">
                        {link.title}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
