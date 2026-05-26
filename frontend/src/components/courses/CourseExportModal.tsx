import { motion } from 'framer-motion'
import { useExportCourses } from '@/hooks/useCourses'
import { showToast } from '@/components/shared/Toast'

interface Props {
  onClose: () => void
  selectedCourseIds: number[]
  selectedCount: number
}

export default function CourseExportModal({ onClose, selectedCourseIds, selectedCount }: Props) {
  const exportMutation = useExportCourses()
  const hasSelection = selectedCourseIds.length > 0

  const handleExport = () => {
    const params = hasSelection ? { course_ids: selectedCourseIds.join(',') } : undefined

    exportMutation.mutate(params, {
      onSuccess: (blob) => {
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        const timestamp = new Date().toISOString().replace(/[-T:]/g, '_').slice(0, 15)
        a.download = `khoahoc_export_${timestamp}.xlsx`
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(url)
        showToast('success', 'Xuất file Excel khóa học thành công!')
        onClose()
      },
      onError: (err: any) => {
        showToast('error', `Xuất file thất bại: ${err.message}`)
      },
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-emerald-50 to-teal-50/30">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-emerald-500 rounded-lg text-white">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
            </div>
            <div>
              <h3 className="font-bold text-gray-900 text-base">Xuất danh sách khóa học ra Excel</h3>
              <p className="text-xs text-gray-500">Một file .xlsx gồm tổng hợp khóa học và danh sách học viên theo từng khóa</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors">
            <svg className="w-5 h-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div className="p-4 rounded-2xl border border-emerald-100 bg-emerald-50/70">
            <p className="text-sm font-semibold text-emerald-900">
              {hasSelection ? `Đang chuẩn bị xuất ${selectedCount} khóa học đã tick chọn.` : 'Chưa tick khóa học nào, hệ thống sẽ xuất toàn bộ khóa học.'}
            </p>
            <p className="text-xs text-emerald-700 mt-1">
              Mỗi khóa học trong file sẽ có số lượng học viên riêng và một sheet chi tiết danh sách học viên của khóa đó.
            </p>
          </div>

          <div className="rounded-2xl border border-gray-100 bg-gray-50/60 p-4 space-y-2 text-sm text-gray-600">
            <p>Sheet 1: Tổng hợp các khóa học và số học viên từng khóa.</p>
            <p>Các sheet tiếp theo: Chi tiết học viên của từng khóa đã chọn.</p>
          </div>

          <div className="flex justify-end gap-3 pt-2 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-sm font-medium text-gray-500 hover:bg-gray-50 hover:text-gray-700 transition-colors"
            >
              Hủy
            </button>
            <button
              type="button"
              onClick={handleExport}
              disabled={exportMutation.isPending}
              className="flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 text-white text-sm font-semibold hover:shadow-lg hover:from-emerald-600 hover:to-teal-700 transition-all disabled:opacity-60 disabled:pointer-events-none"
            >
              {exportMutation.isPending ? (
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
        </div>
      </motion.div>
    </div>
  )
}
