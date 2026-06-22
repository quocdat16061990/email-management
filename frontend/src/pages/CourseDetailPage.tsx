import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useCourseDetail } from '../hooks/useCourses'
import { useEnrollStudent } from '../hooks/useCourses'
import StatusBadge from '../components/shared/StatusBadge'
import LoadingSpinner from '../components/shared/LoadingSpinner'
import ErrorState from '../components/shared/ErrorState'
import { showToast } from '../components/shared/Toast'
import type { CourseLink } from '../types/course'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const quickEnrollSchema = z.object({
  enrollEmail: z.string()
    .trim()
    .min(1, 'Email không được để trống')
    .email('Email không đúng định dạng'),
  enrollName: z.string().trim().optional(),
  enrollPhone: z.string().trim().optional(),
})

type QuickEnrollValues = z.infer<typeof quickEnrollSchema>

export default function CourseDetailPage() {
  const { id } = useParams<{ id: string }>()
  const courseId = id ? parseInt(id) : null
  const { data, isLoading, isError, refetch } = useCourseDetail(courseId)

  // Quick enroll inline
  const [showEnroll, setShowEnroll] = useState(false)
  const enrollMutation = useEnrollStudent()

  const { register, handleSubmit: handleFormSubmit, formState: { errors: formErrors }, reset } = useForm<QuickEnrollValues>({
    resolver: zodResolver(quickEnrollSchema),
    defaultValues: {
      enrollEmail: '',
      enrollName: '',
      enrollPhone: '',
    },
  })

  if (isLoading) return <LoadingSpinner />
  if (isError || !data) return <ErrorState onRetry={() => refetch()} />

  const { course, student_count, students } = data

  const onSubmit = (data: QuickEnrollValues) => {
    enrollMutation.mutate({
      course_id: course.id,
      customer_email: data.enrollEmail.trim(),
      full_name: data.enrollName?.trim() || '',
      phone_number: data.enrollPhone?.trim() || '',
      registration_date: new Date().toISOString().split('T')[0],
      expiry_date: new Date(new Date().setFullYear(new Date().getFullYear() + 1)).toISOString().split('T')[0],
      status: 'ACTIVE',
    }, {
      onSuccess: () => {
        showToast('success', 'Đã thêm học viên.')
        setShowEnroll(false)
        reset()
        refetch()
      },
      onError: (err: Error) => showToast('error', err.message),
    })
  }

  return (
    <div className="space-y-6">
      {/* Back */}
      <Link to="/courses" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-brand-600 transition-colors">
        <svg className="w-4 h-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/></svg>
        Quay lại Danh sách khóa học
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Course Info Card */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="p-6 text-center">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center text-white text-3xl font-extrabold mx-auto shadow-lg shadow-purple-500/25">
                {course.name.slice(0, 2).toUpperCase()}
              </div>
              <h2 className="mt-3 text-lg font-bold text-gray-900">{course.name}</h2>
              </div>
              <div className="px-6 pb-6 space-y-4">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Mô tả</p>
                <p className="text-sm text-gray-700 mt-0.5">{course.description || 'Chưa có mô tả chi tiết.'}</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Ngày tạo</p>
                <p className="text-sm text-gray-700 mt-0.5">{course.created_at ? new Date(course.created_at).toLocaleDateString('vi-VN') : '-'}</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Tổng số học viên</p>
                <p className="text-xl font-bold text-brand-600">{student_count} học viên</p>
              </div>
              {/* Links */}
              {(course.web_link || (course.links && course.links.length > 0)) && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Liên kết học tập</p>
                  <div className="flex flex-col gap-2">
                    {course.web_link && (
                      <a href={course.web_link} target="_blank" rel="noopener noreferrer"
                        className="flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-brand-500 text-white text-xs font-medium hover:bg-brand-600 transition-colors">
                        <svg className="w-3.5 h-3.5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                        Website Khóa Học
                      </a>
                    )}
                    {(course.links || []).map((link: CourseLink, i: number) => (
                      <a key={i} href={link.url} target="_blank" rel="noopener noreferrer"
                        className="flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-purple-200 text-purple-700 text-xs font-medium hover:bg-purple-50 transition-colors">
                        {link.title}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Students list */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-gray-900">Danh sách học viên đăng ký</h3>
              <p className="text-sm text-gray-500">Hiển thị danh sách học viên đang đăng ký khóa học.</p>
            </div>
            <button onClick={() => setShowEnroll(!showEnroll)}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-brand-500 to-accent-600 text-white text-sm font-medium hover:shadow-lg transition-all shadow-sm">
              + Thêm học viên
            </button>
          </div>

          {/* Enroll form inline */}
          {showEnroll && (
            <form onSubmit={handleFormSubmit(onSubmit)} className="bg-white rounded-xl border border-brand-200 shadow-sm p-5 space-y-3">
              <h4 className="font-bold text-brand-700 text-sm">Đăng ký học viên vào khóa học</h4>
              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label className="block text-xs font-medium text-gray-600 mb-0.5">Email <span className="text-red-500">*</span></label>
                  <input type="text" {...register('enrollEmail')}
                    className={`w-full px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 ${
                      formErrors.enrollEmail ? 'border-red-300 focus:border-red-300' : 'border-gray-200 focus:border-brand-300'
                    }`} />
                  {formErrors.enrollEmail && <p className="mt-1 text-xs text-red-500">{formErrors.enrollEmail.message}</p>}
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-0.5">Số điện thoại</label>
                  <input type="text" {...register('enrollPhone')}
                    className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20" />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs font-medium text-gray-600 mb-0.5">Họ và Tên</label>
                  <input type="text" {...register('enrollName')}
                    className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20" />
                </div>
                <div className="flex items-end">
                  <button type="submit" disabled={enrollMutation.isPending}
                    className="w-full px-4 py-2 rounded-lg bg-brand-500 text-white text-sm font-medium hover:bg-brand-600 disabled:opacity-60">
                    {enrollMutation.isPending ? 'Đang xử lý...' : 'Xác nhận'}
                  </button>
                </div>
              </div>
            </form>
          )}

          {/* Student table */}
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50/50">
                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Học viên</th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Email</th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Ngày đăng ký</th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Ngày hết hạn</th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Trạng thái</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {(!students || students.length === 0) ? (
                    <tr><td colSpan={5} className="text-center py-8 text-sm text-gray-400 italic">Chưa có học viên nào đăng ký.</td></tr>
                  ) : (
                    students.map((s, i: number) => (
                      <tr key={i} className="hover:bg-gray-50/50 transition-colors">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-500 to-accent-600 flex items-center justify-center text-white text-xs font-bold">
                              {(s.name || 'HV').slice(0, 2).toUpperCase()}
                            </div>
                            <span className="text-sm font-medium text-gray-900">{s.name || 'Chưa cập nhật'}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">{s.email}</td>
                        <td className="px-4 py-3 text-sm text-gray-500">{s.registration_date ? new Date(s.registration_date).toLocaleDateString('vi-VN') : '-'}</td>
                        <td className="px-4 py-3 text-sm text-gray-500">{s.expiry_date ? new Date(s.expiry_date).toLocaleDateString('vi-VN') : '-'}</td>
                        <td className="px-4 py-3"><StatusBadge status={s.status || 'ACTIVE'} /></td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
