import { useState, useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import { useExportStudents } from '@/hooks/useStudents'
import { showToast } from '@/components/shared/Toast'

interface CourseOption {
  id: number
  name: string
}

interface ExportFormValues {
  export_type: 'simple' | 'full'
  status: 'ALL' | 'ACTIVE' | 'PENDING' | 'EXPIRED'
  course_ids: number[]
  q: string
}

interface Props {
  onClose: () => void
  selectedStudentIds: number[]
  courses: CourseOption[]
  currentFilters?: {
    q?: string
    status?: string
    course_ids?: string
  }
}

export default function ExportModal({ onClose, selectedStudentIds, courses, currentFilters }: Props) {
  const exportMutation = useExportStudents()
  const [courseSearch, setCourseSearch] = useState('')

  // Map initial filters to default values
  const defaultCourseIds = useMemo(() => {
    if (currentFilters?.course_ids) {
      return currentFilters.course_ids
        .split(',')
        .map((id) => parseInt(id.trim()))
        .filter((id) => !isNaN(id))
    }
    return []
  }, [currentFilters?.course_ids])

  const { register, handleSubmit, watch, setValue } = useForm<ExportFormValues>({
    defaultValues: {
      export_type: 'simple',
      status: (currentFilters?.status as any) || 'ALL',
      course_ids: defaultCourseIds,
      q: currentFilters?.q || '',
    },
  })

  const exportType = watch('export_type')
  const status = watch('status')
  const selectedCourseIds = watch('course_ids') || []

  // Filter courses locally in UI search
  const filteredCourses = useMemo(() => {
    if (!courseSearch.trim()) return courses
    const term = courseSearch.toLowerCase()
    return courses.filter((c) => c.name.toLowerCase().includes(term))
  }, [courses, courseSearch])

  const toggleCourse = (id: number) => {
    const next = [...selectedCourseIds]
    const idx = next.indexOf(id)
    if (idx > -1) {
      next.splice(idx, 1)
    } else {
      next.push(id)
    }
    setValue('course_ids', next)
  }

  const selectAllCourses = () => {
    setValue('course_ids', courses.map((c) => c.id))
  }

  const clearAllCourses = () => {
    setValue('course_ids', [])
  }

  const onSubmit = (data: ExportFormValues) => {
    const params: any = {
      export_type: data.export_type,
    }

    // If specific students are ticked on table, export only those and ignore dashboard filters
    if (selectedStudentIds.length > 0) {
      params.student_ids = selectedStudentIds.join(',')
    } else {
      if (data.q?.trim()) params.q = data.q.trim()
      if (data.status !== 'ALL') params.status = data.status
      if (data.course_ids && data.course_ids.length > 0) {
        params.course_ids = data.course_ids.join(',')
      }
    }

    exportMutation.mutate(params, {
      onSuccess: (blob) => {
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        const timestamp = new Date().toISOString().replace(/[-T:]/g, '_').slice(0, 15)
        a.download = `hocvien_export_${timestamp}.xlsx`
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(url)
        showToast('success', 'Xuất file Excel thành công!')
        onClose()
      },
      onError: (err: any) => {
        showToast('error', `Xuất file thất bại: ${err.message}`)
      },
    })
  }

  const isExporting = exportMutation.isPending
  const hasSelection = selectedStudentIds.length > 0

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-emerald-50 to-teal-50/30">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-emerald-500 rounded-lg text-white">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v16.5c0 .621.504 1.125 1.125 1.125h14.25c.621 0 1.125-.504 1.125-1.125V9M3.75 3h1.5m-1.5 0c-.621 0-1.125.504-1.125 1.125v15c0 .621.504 1.125 1.125 1.125M7.5 7.5h7.5m-7.5 3h7.5m-7.5 3h7.5m-7.5 3h7.5M21 9l-6-6m6 6v15M15 3v6h6" />
              </svg>
            </div>
            <div>
              <h3 className="font-bold text-gray-900 text-base">Xuất danh sách ra Excel</h3>
              <p className="text-xs text-gray-500">Tải xuống tệp tin dạng bảng .xlsx</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors">
            <svg className="w-5 h-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-5">
          {/* Active selection badge */}
          {hasSelection ? (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-start gap-3">
              <div className="mt-0.5 p-1 bg-emerald-500 rounded-full text-white">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="3">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold text-emerald-900">Chế độ xuất học viên đã chọn</p>
                <p className="text-xs text-emerald-700 mt-0.5">
                  Đang xuất <strong>{selectedStudentIds.length}</strong> học viên được tick chọn trên bảng danh sách. Các bộ lọc tìm kiếm và khóa học sẽ bị bỏ qua.
                </p>
              </div>
            </div>
          ) : null}

          {/* Export Type (Simple vs Full) */}
          <div>
            <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Định dạng file Excel</label>
            <div className="grid grid-cols-2 gap-3">
              <label
                className={`flex flex-col p-3 rounded-xl border-2 cursor-pointer transition-all ${
                  exportType === 'simple'
                    ? 'border-emerald-500 bg-emerald-50/30'
                    : 'border-gray-100 hover:border-gray-200 bg-white'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-gray-800">Tên & Email</span>
                  <input type="radio" value="simple" {...register('export_type')} className="sr-only" />
                  <div
                    className={`w-4.5 h-4.5 rounded-full border flex items-center justify-center ${
                      exportType === 'simple' ? 'border-emerald-500 bg-emerald-500' : 'border-gray-300'
                    }`}
                  >
                    {exportType === 'simple' && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                  </div>
                </div>
                <span className="text-xs text-gray-500 mt-1">Gồm: STT, Họ và tên, địa chỉ Email. Thích hợp để gửi mail loạt.</span>
              </label>

              <label
                className={`flex flex-col p-3 rounded-xl border-2 cursor-pointer transition-all ${
                  exportType === 'full'
                    ? 'border-emerald-500 bg-emerald-50/30'
                    : 'border-gray-100 hover:border-gray-200 bg-white'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-gray-800">Đầy đủ thông tin</span>
                  <input type="radio" value="full" {...register('export_type')} className="sr-only" />
                  <div
                    className={`w-4.5 h-4.5 rounded-full border flex items-center justify-center ${
                      exportType === 'full' ? 'border-emerald-500 bg-emerald-500' : 'border-gray-300'
                    }`}
                  >
                    {exportType === 'full' && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                  </div>
                </div>
                <span className="text-xs text-gray-500 mt-1">Gồm đầy đủ: Tên, Email, SĐT, Trạng thái, Ngày đăng ký, Hết hạn, Tên các khóa học.</span>
              </label>
            </div>
          </div>

          {/* Filters - Hidden if specific students are selected */}
          {!hasSelection && (
            <div className="space-y-4">
              <div className="border-t border-gray-100 my-2" />

              {/* Status */}
              <div>
                <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Trạng thái học viên</label>
                <select
                  {...register('status')}
                  className="w-full px-3 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white"
                >
                  <option value="ALL">Tất cả trạng thái</option>
                  <option value="ACTIVE">Đang hoạt động</option>
                  <option value="PENDING">Chờ xử lý</option>
                  <option value="EXPIRED">Đã hết hạn</option>
                </select>
              </div>

              {/* Courses checklist with search */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider">Khóa học</label>
                  <div className="flex gap-2 text-xs font-medium text-emerald-600">
                    <button type="button" onClick={selectAllCourses} className="hover:underline">
                      Chọn tất cả
                    </button>
                    <span className="text-gray-300">|</span>
                    <button type="button" onClick={clearAllCourses} className="hover:underline">
                      Bỏ chọn tất cả
                    </button>
                  </div>
                </div>

                {/* Course filter search */}
                <div className="relative mb-2">
                  <input
                    type="text"
                    value={courseSearch}
                    onChange={(e) => setCourseSearch(e.target.value)}
                    placeholder="Tìm nhanh khóa học..."
                    className="w-full px-3 py-1.5 pl-8 rounded-lg border border-gray-200 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                  />
                  <div className="absolute left-2.5 top-2 text-gray-400">
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                </div>

                {/* Checklist container */}
                <div className="space-y-1.5 max-h-40 overflow-y-auto border border-gray-100 rounded-xl p-3 bg-gray-50/30">
                  {filteredCourses.map((c) => {
                    const checked = selectedCourseIds.includes(c.id)
                    return (
                      <label
                        key={c.id}
                        className={`flex items-center gap-2.5 px-2 py-1.5 rounded-lg cursor-pointer transition-colors ${
                          checked ? 'bg-emerald-50/50' : 'hover:bg-gray-50'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => toggleCourse(c.id)}
                          className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 w-3.5 h-3.5"
                        />
                        <span className="text-xs font-medium text-gray-700 line-clamp-1">{c.name}</span>
                      </label>
                    )
                  })}
                  {filteredCourses.length === 0 && (
                    <p className="text-xs text-gray-400 text-center py-4 italic">Không tìm thấy khóa học nào phù hợp.</p>
                  )}
                </div>
                <p className="text-[10px] text-gray-400 mt-1">
                  Đã chọn {selectedCourseIds.length} / {courses.length} khóa học. Nếu không chọn khóa nào, tệp tin sẽ xuất học viên từ tất cả các khóa.
                </p>
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="flex justify-end gap-3 pt-2 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-sm font-medium text-gray-500 hover:bg-gray-50 hover:text-gray-700 transition-colors"
            >
              Hủy
            </button>
            <button
              type="submit"
              disabled={isExporting}
              className="flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 text-white text-sm font-semibold hover:shadow-lg hover:from-emerald-600 hover:to-teal-700 transition-all disabled:opacity-60 disabled:pointer-events-none"
            >
              {isExporting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Đang tải file...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                  </svg>
                  Tải file Excel
                </>
              )}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  )
}
