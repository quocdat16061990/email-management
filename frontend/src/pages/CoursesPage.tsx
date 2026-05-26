import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useCourseList, useDeleteCourse, useSyncCourses, useUpdateWebsite } from '../hooks/useCourses'
import Pagination from '../components/shared/Pagination'
import LoadingSpinner from '../components/shared/LoadingSpinner'
import EmptyState from '../components/shared/EmptyState'
import ErrorState from '../components/shared/ErrorState'
import { showToast } from '../components/shared/Toast'
import CourseFormModal from '../components/courses/CourseFormModal'
import EnrollStudentModal from '../components/courses/EnrollStudentModal'
import CourseExportModal from '../components/courses/CourseExportModal'

export default function CoursesPage() {
  const [page, setPage] = useState(1)
  const [showForm, setShowForm] = useState(false)
  const [showExportModal, setShowExportModal] = useState(false)
  const [editCourse, setEditCourse] = useState<any>(null)
  const [enrollCourseId, setEnrollCourseId] = useState<number | null>(null)
  const [enrollCourseName, setEnrollCourseName] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [selectedIds, setSelectedIds] = useState<number[]>([])

  const { data, isLoading, isError, refetch } = useCourseList({
    page,
    sort_by: sortBy,
    sort_order: sortOrder,
  })
  const deleteMutation = useDeleteCourse()
  const syncMutation = useSyncCourses()
  const updateWebsiteMutation = useUpdateWebsite()

  const [editingWebsite, setEditingWebsite] = useState<{ id: number; name: string; url: string } | null>(null)

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('asc')
    }
    setPage(1)
  }

  const handleDelete = (id: number, name: string) => {
    if (!window.confirm(`Bạn có chắc muốn xóa khóa học "${name}"?`)) return
    deleteMutation.mutate(id, {
      onSuccess: () => showToast('success', 'Đã xóa khóa học.'),
      onError: (err: any) => showToast('error', err.message),
    })
  }

  const handleSync = () => {
    syncMutation.mutate(undefined, {
      onSuccess: (res) => showToast('success', `Đồng bộ thành công! ${res.result.total} khóa học.`),
      onError: (err: any) => showToast('error', err.message),
    })
  }

  const handleSaveWebsite = () => {
    if (!editingWebsite) return
    updateWebsiteMutation.mutate(
      { id: editingWebsite.id, web_link: editingWebsite.url },
      {
        onSuccess: () => {
          showToast('success', 'Đã cập nhật website.')
          setEditingWebsite(null)
        },
        onError: (err: any) => showToast('error', err.message),
      },
    )
  }

  const allIdsOnPage = data?.courses.map((course) => course.id) || []
  const isAllSelectedOnPage = allIdsOnPage.length > 0 && allIdsOnPage.every((id) => selectedIds.includes(id))

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Danh sách khóa học</h2>
          <p className="text-sm text-gray-500">Quản lý các chương trình học tập đang hoạt động.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setShowExportModal(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 text-white text-sm font-medium hover:bg-emerald-600 transition-all shadow-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            <span>{selectedIds.length > 0 ? `Xuất Excel (${selectedIds.length} đã chọn)` : 'Xuất Excel'}</span>
          </button>
          <button
            onClick={handleSync}
            disabled={syncMutation.isPending}
            className="px-4 py-2 rounded-xl bg-emerald-500 text-white text-sm font-medium hover:bg-emerald-600 transition-all shadow-sm disabled:opacity-60"
          >
            {syncMutation.isPending ? 'Đang đồng bộ...' : 'Đồng bộ từ Voomly'}
          </button>
          <button
            onClick={() => {
              setEditCourse(null)
              setShowForm(true)
            }}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-brand-500 to-accent-600 text-white text-sm font-medium hover:shadow-lg hover:-translate-y-0.5 transition-all shadow-sm"
          >
            + Thêm khóa học
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50/50 select-none">
                <th className="px-3 py-3 w-10 text-center">
                  <input
                    type="checkbox"
                    checked={isAllSelectedOnPage}
                    onChange={() => {
                      if (isAllSelectedOnPage) {
                        setSelectedIds((prev) => prev.filter((id) => !allIdsOnPage.includes(id)))
                        return
                      }
                      setSelectedIds((prev) => {
                        const next = [...prev]
                        allIdsOnPage.forEach((id) => {
                          if (!next.includes(id)) next.push(id)
                        })
                        return next
                      })
                    }}
                    className="rounded border-gray-300 text-brand-500 focus:ring-brand-500 w-4 h-4 cursor-pointer"
                  />
                </th>
                <th
                  onClick={() => handleSort('name')}
                  className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:text-brand-600 hover:bg-gray-100/50 transition-colors"
                >
                  <div className="flex items-center gap-0.5">
                    Khóa học
                    {sortBy === 'name' && (sortOrder === 'asc' ? ' ▲' : ' ▼')}
                  </div>
                </th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Website</th>
                <th
                  onClick={() => handleSort('student_count')}
                  className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:text-brand-600 hover:bg-gray-100/50 transition-colors"
                >
                  <div className="flex items-center gap-0.5">
                    Học viên
                    {sortBy === 'student_count' && (sortOrder === 'asc' ? ' ▲' : ' ▼')}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('created_at')}
                  className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:text-brand-600 hover:bg-gray-100/50 transition-colors"
                >
                  <div className="flex items-center gap-0.5">
                    Ngày tạo
                    {sortBy === 'created_at' && (sortOrder === 'asc' ? ' ▲' : ' ▼')}
                  </div>
                </th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {isLoading && (
                <tr>
                  <td colSpan={6}>
                    <LoadingSpinner />
                  </td>
                </tr>
              )}
              {isError && (
                <tr>
                  <td colSpan={6}>
                    <ErrorState onRetry={() => refetch()} />
                  </td>
                </tr>
              )}
              {data?.courses.length === 0 && (
                <tr>
                  <td colSpan={6}>
                    <EmptyState text="Chưa có khóa học nào." />
                  </td>
                </tr>
              )}
              {data?.courses.map((course) => {
                const isChecked = selectedIds.includes(course.id)
                return (
                  <tr key={course.id} className={`hover:bg-gray-50/50 transition-colors ${isChecked ? 'bg-brand-50/20' : ''}`}>
                    <td className="px-3 py-3 text-center">
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {
                          setSelectedIds((prev) =>
                            prev.includes(course.id) ? prev.filter((id) => id !== course.id) : [...prev, course.id]
                          )
                        }}
                        className="rounded border-gray-300 text-brand-500 focus:ring-brand-500 w-4 h-4 cursor-pointer"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <Link to={`/courses/${course.id}`} className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center text-white text-xs font-bold">
                          {course.name.slice(0, 2).toUpperCase()}
                        </div>
                        <span className="font-medium text-gray-900 text-sm hover:text-brand-600">{course.name}</span>
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {course.web_link ? (
                          <a href={course.web_link} target="_blank" rel="noopener noreferrer" className="text-xs text-brand-600 hover:text-brand-700 font-medium">
                            Truy cập
                          </a>
                        ) : (
                          <span className="text-xs text-gray-400 italic">Chưa cấu hình</span>
                        )}
                        <button
                          onClick={() => setEditingWebsite({ id: course.id, name: course.name, url: course.web_link || '' })}
                          className="p-1 rounded text-gray-300 hover:text-brand-500"
                        >
                          <svg className="w-3.5 h-3.5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M12 20h9" />
                            <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
                          </svg>
                        </button>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-100">
                        {course.student_count || 0} học viên
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {course.created_at ? new Date(course.created_at).toLocaleDateString('vi-VN') : '-'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => {
                            setEnrollCourseId(course.id)
                            setEnrollCourseName(course.name)
                          }}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-brand-600 hover:bg-brand-50 transition-colors"
                          title="Thêm học viên"
                        >
                          <svg className="w-4 h-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M12 5v14M5 12h14" />
                          </svg>
                        </button>
                        <button
                          onClick={() => {
                            setEditCourse(course)
                            setShowForm(true)
                          }}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-brand-600 hover:bg-brand-50 transition-colors"
                          title="Chỉnh sửa"
                        >
                          <svg className="w-4 h-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M12 20h9" />
                            <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDelete(course.id, course.name)}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                          title="Xóa"
                        >
                          <svg className="w-4 h-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M3 6h18" />
                            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        {data?.pagination && (
          <div className="px-4 py-3 border-t border-gray-100">
            <Pagination pagination={data.pagination} onPageChange={setPage} />
          </div>
        )}
      </div>

      {editingWebsite && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm" onClick={() => setEditingWebsite(null)}>
          <div className="w-full max-w-sm bg-white rounded-2xl shadow-2xl border p-6" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-bold text-gray-900 mb-1">Cập nhật Link Website</h3>
            <p className="text-sm text-gray-500 mb-4">
              Khóa học: <span className="font-medium text-gray-700">{editingWebsite.name}</span>
            </p>
            <input
              type="url"
              value={editingWebsite.url}
              onChange={(e) => setEditingWebsite({ ...editingWebsite, url: e.target.value })}
              placeholder="https://example.com/course"
              className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            />
            <div className="flex justify-end gap-3">
              <button onClick={() => setEditingWebsite(null)} className="px-4 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100">
                Hủy
              </button>
              <button
                onClick={handleSaveWebsite}
                disabled={updateWebsiteMutation.isPending}
                className="px-4 py-2 rounded-lg bg-brand-500 text-white text-sm font-medium hover:bg-brand-600 disabled:opacity-60"
              >
                {updateWebsiteMutation.isPending ? 'Đang lưu...' : 'Lưu'}
              </button>
            </div>
          </div>
        </div>
      )}

      {showForm && (
        <CourseFormModal
          course={editCourse}
          onClose={() => setShowForm(false)}
          onSuccess={() => {
            setShowForm(false)
            refetch()
          }}
        />
      )}

      {enrollCourseId && (
        <EnrollStudentModal
          courseId={enrollCourseId}
          courseName={enrollCourseName}
          onClose={() => {
            setEnrollCourseId(null)
            setEnrollCourseName('')
          }}
          onSuccess={() => {
            setEnrollCourseId(null)
            refetch()
          }}
        />
      )}

      {showExportModal && (
        <CourseExportModal
          selectedCourseIds={selectedIds}
          selectedCount={selectedIds.length}
          onClose={() => setShowExportModal(false)}
        />
      )}
    </div>
  )
}
