import { useState, useMemo } from 'react'
import { useStudentSearch } from '../../hooks/useStudents'
import { useEnrollStudent } from '../../hooks/useCourses'
import { showToast } from '../shared/Toast'
import type { StudentSearchResult } from '../../types/student'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

interface Props {
  courseId: number
  courseName: string
  onClose: () => void
  onSuccess: () => void
}

type EnrollFormValues = {
  customer_email?: string
  full_name?: string
  phone_number?: string
  registration_date: string
  expiry_date: string
  status: string
}

export default function EnrollStudentModal({ courseId, courseName, onClose, onSuccess }: Props) {
  const [mode, setMode] = useState<'search' | 'new'>('search')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchPage, setSearchPage] = useState(1)
  const [selectedStudent, setSelectedStudent] = useState<StudentSearchResult | null>(null)

  const { data: searchData, isLoading: searchLoading } = useStudentSearch({
    course_id: courseId,
    q: searchQuery || undefined,
    page: searchPage,
  })

  const enrollMutation = useEnrollStudent()

  const schema = useMemo(() => {
    return z.object({
      customer_email: z.string().trim().optional(),
      full_name: z.string().trim().optional(),
      phone_number: z.string().trim().optional(),
      registration_date: z.string().min(1, 'Ngày đăng ký không được để trống'),
      expiry_date: z.string().min(1, 'Ngày hết hạn không được để trống'),
      status: z.string().min(1, 'Trạng thái không được để trống'),
    }).superRefine((data, ctx) => {
      if (!selectedStudent) {
        if (!data.customer_email) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ['customer_email'],
            message: 'Email không được để trống',
          })
        } else if (!z.string().email().safeParse(data.customer_email).success) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ['customer_email'],
            message: 'Email không đúng định dạng',
          })
        }
      }
    })
  }, [selectedStudent])

  const { register, handleSubmit, formState: { errors } } = useForm<EnrollFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      customer_email: '',
      full_name: '',
      phone_number: '',
      registration_date: new Date().toISOString().split('T')[0],
      expiry_date: (() => {
        const d = new Date()
        d.setFullYear(d.getFullYear() + 1)
        return d.toISOString().split('T')[0]
      })(),
      status: 'ACTIVE',
    },
  })

  const handleSelectStudent = (student: StudentSearchResult) => {
    setSelectedStudent(student)
    setMode('search')
  }

  const onSubmit = (data: EnrollFormValues) => {
    if (selectedStudent) {
      enrollMutation.mutate({
        course_id: courseId,
        student_id: selectedStudent.id,
        registration_date: data.registration_date,
        expiry_date: data.expiry_date,
        status: data.status,
      }, {
        onSuccess: () => {
          showToast('success', 'Đã đăng ký học viên vào khóa học.')
          onSuccess()
        },
        onError: (err: Error) => showToast('error', err.message),
      })
    } else {
      enrollMutation.mutate({
        course_id: courseId,
        customer_email: data.customer_email?.trim() || '',
        full_name: data.full_name?.trim() || '',
        phone_number: data.phone_number?.trim() || '',
        registration_date: data.registration_date,
        expiry_date: data.expiry_date,
        status: data.status,
      }, {
        onSuccess: () => {
          showToast('success', 'Đã thêm học viên vào khóa học.')
          onSuccess()
        },
        onError: (err: Error) => showToast('error', err.message),
      })
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-12 bg-black/30 backdrop-blur-sm" onClick={onClose}>
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl border overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div>
            <h3 className="font-bold text-gray-900">Đăng ký học viên</h3>
            <p className="text-sm text-gray-500">Khóa học: <span className="font-medium text-purple-700">{courseName}</span></p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100">
            <svg className="w-5 h-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 max-h-[70vh] overflow-y-auto space-y-4">
          {/* Search existing students */}
          {mode === 'search' && !selectedStudent && (
            <>
              <div className="relative">
                <input type="text" value={searchQuery} onChange={(e) => { setSearchQuery(e.target.value); setSearchPage(1) }}
                  placeholder="Tìm kiếm học viên theo tên, email..."
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20" />
                <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
              </div>

              <div className="max-h-60 overflow-y-auto border border-gray-100 rounded-xl">
                {searchLoading && <p className="text-center py-4 text-sm text-gray-400">Đang tải...</p>}
                {searchData?.students.length === 0 && <p className="text-center py-4 text-sm text-gray-400 italic">Không tìm thấy học viên.</p>}
                {searchData?.students.map((s) => (
                  <div key={s.id} className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 border-b border-gray-50 last:border-0">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{s.full_name || 'Chưa cập nhật'}</p>
                      <p className="text-xs text-gray-500">{s.customer_email}</p>
                    </div>
                    {s.is_enrolled ? (
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-100">Đã đăng ký</span>
                    ) : (
                      <button type="button" onClick={() => handleSelectStudent(s)} className="px-3 py-1 rounded-lg bg-brand-500 text-white text-xs font-medium hover:bg-brand-600">Chọn</button>
                    )}
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {searchData?.pagination && searchData.pagination.total_pages > 1 && (
                <div className="flex items-center justify-center gap-1">
                  <button type="button" onClick={() => setSearchPage((p) => Math.max(1, p - 1))} disabled={!searchData.pagination.has_prev}
                    className="px-3 py-1 text-xs rounded text-gray-600 hover:bg-gray-100 disabled:text-gray-300">Trước</button>
                  <span className="text-xs text-gray-500">Trang {searchData.pagination.current_page}/{searchData.pagination.total_pages}</span>
                  <button type="button" onClick={() => setSearchPage((p) => p + 1)} disabled={!searchData.pagination.has_next}
                    className="px-3 py-1 text-xs rounded text-gray-600 hover:bg-gray-100 disabled:text-gray-300">Sau</button>
                </div>
              )}

              <div className="text-center pt-2 border-t border-gray-100">
                <button type="button" onClick={() => setMode('new')} className="text-sm text-brand-600 hover:text-brand-700 font-medium">
                  + Tạo học viên mới
                </button>
              </div>
            </>
          )}

          {/* Selected student info */}
          {selectedStudent && (
            <div className="p-4 rounded-xl bg-brand-50 border border-brand-100 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">{selectedStudent.full_name || 'Học viên'}</p>
                <p className="text-xs text-gray-500">{selectedStudent.customer_email}</p>
              </div>
              <button type="button" onClick={() => setSelectedStudent(null)} className="text-xs text-brand-600 hover:text-brand-700 font-medium">Chọn học viên khác</button>
            </div>
          )}

          {/* New student form */}
          {mode === 'new' && !selectedStudent && (
            <div className="p-4 rounded-xl border border-brand-200 bg-brand-50/50 space-y-3">
              <h4 className="text-sm font-bold text-brand-700">Tạo học viên mới</h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2">
                  <label className="block text-xs font-medium text-gray-600 mb-0.5">Email <span className="text-red-500">*</span></label>
                  <input type="text" {...register('customer_email')}
                    className={`w-full px-3 py-1.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 ${
                      errors.customer_email ? 'border-red-300 focus:border-red-300' : 'border-gray-200 focus:border-brand-300'
                    }`} />
                  {errors.customer_email && <p className="mt-1 text-xs text-red-500">{errors.customer_email.message}</p>}
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-0.5">Họ và Tên</label>
                  <input type="text" {...register('full_name')}
                    className="w-full px-3 py-1.5 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-0.5">Số điện thoại</label>
                  <input type="text" {...register('phone_number')}
                    className="w-full px-3 py-1.5 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20" />
                </div>
              </div>
              <button type="button" onClick={() => setMode('search')} className="text-xs text-brand-600 hover:text-brand-700 font-medium">Quay lại tìm kiếm</button>
            </div>
          )}

          {/* Enrollment info */}
          {(selectedStudent || mode === 'new') && (
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-0.5">Ngày đăng ký</label>
                <input type="date" {...register('registration_date')}
                  className="w-full px-2 py-1.5 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-0.5">Ngày hết hạn</label>
                <input type="date" {...register('expiry_date')}
                  className="w-full px-2 py-1.5 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-0.5">Trạng thái</label>
                <select {...register('status')}
                  className="w-full px-2 py-1.5 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20">
                  <option value="ACTIVE">Đang hoạt động</option>
                  <option value="PENDING">Chờ xử lý</option>
                  <option value="EXPIRED">Đã hết hạn</option>
                </select>
              </div>
            </div>
          )}

          {/* Submit */}
          <div className="flex justify-end gap-3 pt-2 border-t border-gray-100">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100">Hủy</button>
            <button type="submit" disabled={enrollMutation.isPending}
              className="px-5 py-2 rounded-lg bg-gradient-to-r from-brand-500 to-accent-600 text-white text-sm font-medium hover:shadow-lg disabled:opacity-60">
              {enrollMutation.isPending ? 'Đang xử lý...' : 'Xác nhận đăng ký'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
