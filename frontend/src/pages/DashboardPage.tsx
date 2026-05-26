import { useState, useMemo } from 'react'
import { useStudentList, useDeleteStudent, useSyncStudents } from '@/hooks/useStudents'
import { useCourseList } from '@/hooks/useCourses'
import { useDashboardStats } from '@/hooks/useAuth'
import SearchInput from '@/components/shared/SearchInput'
import Pagination from '@/components/shared/Pagination'
import StatusBadge from '@/components/shared/StatusBadge'
import Avatar from '@/components/shared/Avatar'
import EmptyState from '@/components/shared/EmptyState'
import ErrorState from '@/components/shared/ErrorState'
import { showToast } from '@/components/shared/Toast'
import StudentFormModal from '@/components/students/StudentFormModal'
import ExportModal from '@/components/students/ExportModal'
import { Link } from 'react-router-dom'
import type { Student } from '@/types/student'

export default function DashboardPage() {
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const [searchValue, setSearchValue] = useState('')
  const [editStudent, setEditStudent] = useState<Student | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [showExportModal, setShowExportModal] = useState(false)
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  // Filtering states
  const [selectedCourseIds, setSelectedCourseIds] = useState<number[]>([])
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL')
  const [isCourseFilterOpen, setIsCourseFilterOpen] = useState(false)
  const [courseFilterSearch, setCourseFilterSearch] = useState('')

  // Checkbox selection state
  const [selectedIds, setSelectedIds] = useState<number[]>([])

  const courseIdsParam = useMemo(() => selectedCourseIds.join(','), [selectedCourseIds])

  const { data, isLoading, isFetching, isError, refetch } = useStudentList({
    q: query,
    page,
    sort_by: sortBy,
    sort_order: sortOrder,
    course_ids: courseIdsParam,
    status: selectedStatus,
  })
  const deleteMutation = useDeleteStudent()
  const syncMutation = useSyncStudents()
  
  // Fetch all courses for the filtering dropdowns and Export Modal
  const allCoursesQuery = useCourseList({ all: true })
  const courses = allCoursesQuery.data?.courses || []
  const { data: stats } = useDashboardStats()

  const handleCourseFilterToggle = (id: number) => {
    setSelectedCourseIds((prev) => {
      const next = prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
      setPage(1)
      setSelectedIds([])
      return next
    })
  }

  const handleStatusFilterChange = (status: string) => {
    setSelectedStatus(status)
    setPage(1)
    setSelectedIds([])
  }

  const handleSearch = (val: string) => {
    setSearchValue(val)
    setQuery(val)
    setPage(1)
    setSelectedIds([])
  }

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
    if (!window.confirm(`Bạn có chắc muốn xóa học viên "${name}"?`)) return
    deleteMutation.mutate(id, {
      onSuccess: () => showToast('success', 'Đã xóa học viên thành công.'),
      onError: (err: Error) => showToast('error', err.message),
    })
  }

  const handleSync = () => {
    syncMutation.mutate(undefined, {
      onSuccess: (res) => showToast('success', `Đồng bộ thành công! ${res.result.total_students} học viên.`),
      onError: (err: Error) => showToast('error', err.message),
    })
  }

  const openCreate = () => {
    setEditStudent(null)
    setShowForm(true)
  }

  const openEdit = (student: Student) => {
    setEditStudent(student)
    setShowForm(true)
  }

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Tổng học viên', value: stats?.total_students ?? 0, color: 'from-brand-500 to-brand-600' },
          { label: 'Đang hoạt động', value: stats?.active_count ?? 0, color: 'from-emerald-500 to-emerald-600' },
          { label: 'Chờ xử lý', value: stats?.pending_count ?? 0, color: 'from-amber-500 to-amber-600' },
          { label: 'Đã hết hạn', value: stats?.expired_count ?? 0, color: 'from-red-500 to-red-600' },
        ].map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{stat.label}</p>
            <p className={`mt-1 text-2xl font-bold bg-gradient-to-r ${stat.color} bg-clip-text text-transparent`}>
              {stat.value}
            </p>
          </div>
        ))}
      </div>

      {/* Actions / Filter Toolbar */}
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4 bg-gray-50/50 p-3 rounded-2xl border border-gray-100/80">
        <div className="flex flex-wrap items-center gap-2 flex-1">
          <div className="w-full sm:w-64">
            <SearchInput value={searchValue} onChange={handleSearch} placeholder="Tìm kiếm học viên..." loading={isFetching} />
          </div>
          
          {/* Custom Course Filter Dropdown */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsCourseFilterOpen(!isCourseFilterOpen)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl border border-gray-200 bg-white text-xs font-semibold text-gray-700 hover:bg-gray-50 focus:outline-none cursor-pointer transition-colors shadow-sm"
            >
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <span>Khóa học</span>
              {selectedCourseIds.length > 0 && (
                <span className="flex items-center justify-center min-w-5 h-5 px-1 text-[10px] font-bold text-white bg-brand-500 rounded-full">
                  {selectedCourseIds.length}
                </span>
              )}
              <svg className={`w-3.5 h-3.5 text-gray-400 transition-transform ${isCourseFilterOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
              </svg>
            </button>

            {isCourseFilterOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setIsCourseFilterOpen(false)} />
                <div className="absolute left-0 mt-2 w-72 rounded-2xl bg-white border border-gray-100 shadow-xl z-20 p-3 space-y-2">
                  <div className="relative">
                    <input
                      type="text"
                      value={courseFilterSearch}
                      onChange={(e) => setCourseFilterSearch(e.target.value)}
                      placeholder="Tìm nhanh khóa học..."
                      className="w-full px-2 py-1.5 pl-7 border border-gray-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                    />
                    <div className="absolute left-2.5 top-2.5 text-gray-400">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                    </div>
                  </div>
                  <div className="max-h-48 overflow-y-auto space-y-1 pr-1">
                    {courses
                      .filter((c) => c.name.toLowerCase().includes(courseFilterSearch.toLowerCase()))
                      .map((c) => {
                        const isChecked = selectedCourseIds.includes(c.id)
                        return (
                          <label key={c.id} className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-gray-50 cursor-pointer select-none">
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={() => handleCourseFilterToggle(c.id)}
                              className="rounded border-gray-300 text-brand-500 focus:ring-brand-500 w-3.5 h-3.5 cursor-pointer"
                            />
                            <span className="text-xs font-medium text-gray-700 line-clamp-1">{c.name}</span>
                          </label>
                        )
                      })}
                    {courses.filter((c) => c.name.toLowerCase().includes(courseFilterSearch.toLowerCase())).length === 0 && (
                      <p className="text-xs text-gray-400 text-center py-4 italic">Không tìm thấy khóa học.</p>
                    )}
                  </div>
                  {selectedCourseIds.length > 0 && (
                    <div className="flex justify-between border-t border-gray-100 pt-2 text-[10px] font-bold text-gray-400">
                      <span>Đang chọn {selectedCourseIds.length} khóa</span>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedCourseIds([])
                          setPage(1)
                          setSelectedIds([])
                        }}
                        className="text-brand-500 hover:underline"
                      >
                        Xóa lọc
                      </button>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>

          {/* Status Dropdown Filter */}
          <select
            value={selectedStatus}
            onChange={(e) => handleStatusFilterChange(e.target.value)}
            className="px-3 py-2 rounded-xl border border-gray-200 bg-white text-xs font-semibold text-gray-700 hover:bg-gray-50 focus:outline-none cursor-pointer transition-colors shadow-sm"
          >
            <option value="ALL">Tất cả trạng thái</option>
            <option value="ACTIVE">Đang hoạt động</option>
            <option value="PENDING">Chờ xử lý</option>
            <option value="EXPIRED">Đã hết hạn</option>
          </select>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Export Excel Button */}
          <button
            onClick={() => setShowExportModal(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 text-white text-sm font-semibold hover:bg-emerald-600 transition-all shadow-sm active:scale-95 cursor-pointer"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            <span>{selectedIds.length > 0 ? `Xuất Excel (${selectedIds.length} đã chọn)` : 'Xuất Excel'}</span>
          </button>

          <button onClick={handleSync} disabled={syncMutation.isPending}
            className="px-4 py-2 rounded-xl border border-gray-200 bg-white text-gray-700 text-sm font-medium hover:bg-gray-50 transition-all shadow-sm disabled:opacity-60 cursor-pointer"
          >
            {syncMutation.isPending ? 'Đang đồng bộ...' : 'Đồng bộ từ Voomly'}
          </button>
          
          <button onClick={openCreate}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-brand-500 to-accent-600 text-white text-sm font-semibold hover:shadow-lg hover:-translate-y-0.5 transition-all shadow-sm cursor-pointer"
          >
            + Thêm học viên
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden relative">
        {/* Top fetching progress bar */}
        {isFetching && (
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-brand-50 overflow-hidden z-10">
            <div className="h-full bg-brand-500 animate-pulse w-full" />
          </div>
        )}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50/50 select-none">
                <th className="px-3 py-3 w-10 text-center">
                  <input
                    type="checkbox"
                    checked={data?.students && data.students.length > 0 && data.students.every((s) => selectedIds.includes(s.id))}
                    onChange={() => {
                      const allIdsOnPage = data?.students.map((s) => s.id) || []
                      const isAllSelected = allIdsOnPage.length > 0 && allIdsOnPage.every((id) => selectedIds.includes(id))
                      if (isAllSelected) {
                        setSelectedIds((prev) => prev.filter((id) => !allIdsOnPage.includes(id)))
                      } else {
                        setSelectedIds((prev) => {
                          const next = [...prev]
                          allIdsOnPage.forEach((id) => {
                            if (!next.includes(id)) next.push(id)
                          })
                          return next
                        })
                      }
                    }}
                    className="rounded border-gray-300 text-brand-500 focus:ring-brand-500 w-4 h-4 cursor-pointer"
                  />
                </th>
                <th onClick={() => handleSort('full_name')} className="text-left px-2 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:text-brand-600 hover:bg-gray-100/50 transition-colors">
                  <div className="flex items-center gap-0.5">
                    Học viên
                    {sortBy === 'full_name' && (sortOrder === 'asc' ? ' ▲' : ' ▼')}
                  </div>
                </th>
                <th onClick={() => handleSort('customer_email')} className="text-left px-2 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:text-brand-600 hover:bg-gray-100/50 transition-colors">
                  <div className="flex items-center gap-0.5">
                    Email
                    {sortBy === 'customer_email' && (sortOrder === 'asc' ? ' ▲' : ' ▼')}
                  </div>
                </th>
                <th onClick={() => handleSort('phone_number')} className="text-left px-2 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:text-brand-600 hover:bg-gray-100/50 transition-colors">
                  <div className="flex items-center gap-0.5">
                    Số điện thoại
                    {sortBy === 'phone_number' && (sortOrder === 'asc' ? ' ▲' : ' ▼')}
                  </div>
                </th>
                <th className="text-left px-2 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Khóa học</th>
                <th onClick={() => handleSort('status')} className="text-left px-2 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:text-brand-600 hover:bg-gray-100/50 transition-colors">
                  <div className="flex items-center gap-0.5">
                    Trạng thái
                    {sortBy === 'status' && (sortOrder === 'asc' ? ' ▲' : ' ▼')}
                  </div>
                </th>
                <th onClick={() => handleSort('expiry_date')} className="text-left px-2 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:text-brand-600 hover:bg-gray-100/50 transition-colors">
                  <div className="flex items-center gap-0.5">
                    Hết hạn
                    {sortBy === 'expiry_date' && (sortOrder === 'asc' ? ' ▲' : ' ▼')}
                  </div>
                </th>
                <th className="text-right px-2 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Hành động</th>
              </tr>
            </thead>
            <tbody className={`divide-y divide-gray-50 transition-opacity duration-200 ${isFetching ? 'opacity-50 pointer-events-none' : ''}`}>
              {isLoading && (
                <tr><td colSpan={8}>
                  <div className="flex items-center justify-center py-8 gap-2">
                    <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
                    <span className="text-xs text-gray-400">Đang tải dữ liệu...</span>
                  </div>
                </td></tr>
              )}
              {isError && (
                <tr><td colSpan={8}><ErrorState onRetry={() => refetch()} /></td></tr>
              )}
              {data?.students.length === 0 && (
                <tr><td colSpan={8}><EmptyState text="Không tìm thấy học viên nào." /></td></tr>
              )}
              {data?.students.map((s) => {
                const courseCount = s.enrollments?.length || 0
                const isChecked = selectedIds.includes(s.id)
                return (
                  <tr key={s.id} className={`hover:bg-gray-50/50 transition-colors ${isChecked ? 'bg-brand-50/20' : ''}`}>
                    <td className="px-3 py-3 text-center">
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {
                          setSelectedIds((prev) =>
                            prev.includes(s.id) ? prev.filter((id) => id !== s.id) : [...prev, s.id]
                          )
                        }}
                        className="rounded border-gray-300 text-brand-500 focus:ring-brand-500 w-4 h-4 cursor-pointer"
                      />
                    </td>
                    <td className="px-2 py-3">
                      <div className="flex items-center gap-2">
                        <Avatar name={s.full_name} />
                        <Link to={`/students/${s.id}`} className="font-medium text-gray-900 hover:text-brand-600 text-sm">
                          {s.full_name || 'Chưa cập nhật'}
                        </Link>
                      </div>
                    </td>
                    <td className="px-2 py-3 text-sm text-gray-500">{s.customer_email}</td>
                    <td className="px-2 py-3 text-sm text-gray-500">{s.phone_number || '-'}</td>
                    <td className="px-2 py-3">
                      <div className="flex flex-wrap gap-1">
                        {s.enrollments?.slice(0, 1).map((e) => (
                          <Link key={e.course_id} to={`/courses/${e.course_id}`}
                            className="inline-flex px-1.5 py-0.5 rounded-md bg-purple-50 text-purple-700 text-xs font-medium border border-purple-100 hover:bg-purple-100 transition-colors">
                            {e.course_name}
                          </Link>
                        ))}
                        {courseCount > 1 && (
                          <Link to={`/students/${s.id}`}
                            className="inline-flex px-1.5 py-0.5 rounded-md bg-gray-100 text-gray-500 text-xs font-medium hover:bg-gray-200 transition-colors">
                            +{courseCount - 1}
                          </Link>
                        )}
                      </div>
                    </td>
                    <td className="px-2 py-3"><StatusBadge status={s.status} /></td>
                    <td className="px-2 py-3 text-sm text-gray-500">{s.expiry_date || '-'}</td>
                    <td className="px-2 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => openEdit(s)}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-brand-600 hover:bg-brand-50 transition-colors cursor-pointer"
                          title="Chỉnh sửa"
                        >
                          <svg className="w-4 h-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
                        </button>
                        <button onClick={() => handleDelete(s.id, s.full_name)}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors cursor-pointer"
                          title="Xóa"
                        >
                          <svg className="w-4 h-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
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
          <div className="px-2 py-3 border-t border-gray-100">
            <Pagination pagination={data.pagination} onPageChange={setPage} />
          </div>
        )}
      </div>

      {showForm && (
        <StudentFormModal
          student={editStudent || undefined}
          courses={courses.map((c) => ({ id: c.id, name: c.name }))}
          onClose={() => setShowForm(false)}
          onSuccess={() => {
            setShowForm(false)
            refetch()
          }}
        />
      )}

      {showExportModal && (
        <ExportModal
          courses={courses}
          selectedStudentIds={selectedIds}
          currentFilters={{
            q: query,
            status: selectedStatus,
            course_ids: courseIdsParam,
          }}
          onClose={() => {
            setShowExportModal(false)
          }}
        />
      )}
    </div>
  )
}
