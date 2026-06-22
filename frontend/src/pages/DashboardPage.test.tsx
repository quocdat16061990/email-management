import { describe, test, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DashboardPage from './DashboardPage'
import { useStudentList, useDeleteStudent } from '../hooks/useStudents'
import { useCourseList } from '../hooks/useCourses'
import { fetchDashboardStats } from '../api/auth'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../hooks/useStudents', () => ({
  useStudentList: vi.fn(),
  useDeleteStudent: vi.fn(),
}))

vi.mock('../hooks/useCourses', () => ({
  useCourseList: vi.fn(),
}))

vi.mock('../api/auth', () => ({
  fetchDashboardStats: vi.fn(),
}))

vi.mock('../components/shared/Toast', () => ({
  showToast: vi.fn(),
}))

const queryClient = new QueryClient()

function renderDashboardPage() {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('pages/DashboardPage.tsx', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(useStudentList).mockReturnValue({
      data: {
        students: [
          { id: 1, full_name: 'Test Student', customer_email: 'test@example.com', phone_number: '123456789', status: 'ACTIVE', expiry_date: '2026-12-31', enrollments: [] }
        ],
        pagination: { total_pages: 1, current_page: 1, total_items: 1 }
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any)

    vi.mocked(useDeleteStudent).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any)

    vi.mocked(useCourseList).mockReturnValue({
      data: { courses: [] },
      isLoading: false,
      isError: false,
    } as any)

    vi.mocked(fetchDashboardStats).mockResolvedValue({
      total_students: 10,
      active_count: 8,
      pending_count: 1,
      expired_count: 1,
    } as any)
  })

  test('renders page stats cards and main controls', async () => {
    renderDashboardPage()

    expect(screen.getByText('Tổng học viên')).toBeInTheDocument()
    expect(screen.getAllByText('Đang hoạt động')[0]).toBeInTheDocument()
    expect(screen.getAllByText('Chờ xử lý')[0]).toBeInTheDocument()
    expect(screen.getAllByText('Đã hết hạn')[0]).toBeInTheDocument()

    expect(screen.getByPlaceholderText('Tìm kiếm học viên...')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /\+ Thêm học viên/i })).toBeInTheDocument()
  })

  test('renders student list table successfully', () => {
    renderDashboardPage()

    expect(screen.getByText('Test Student')).toBeInTheDocument()
    expect(screen.getByText('test@example.com')).toBeInTheDocument()
    expect(screen.getByText('123456789')).toBeInTheDocument()
  })

  test('renders loading spinner when loading students', () => {
    vi.mocked(useStudentList).mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    } as any)

    renderDashboardPage()

    expect(screen.getByText('Đang tải dữ liệu...')).toBeInTheDocument()
  })

  test('renders empty state when there are no students', () => {
    vi.mocked(useStudentList).mockReturnValue({
      data: { students: [], pagination: null },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any)

    renderDashboardPage()

    expect(screen.getByText('Không tìm thấy học viên nào.')).toBeInTheDocument()
  })

  test('calls useStudentList with correct sort params when header is clicked', async () => {
    const user = userEvent.setup()
    renderDashboardPage()

    const emailHeader = screen.getByRole('columnheader', { name: /Email/i })
    await user.click(emailHeader)

    expect(useStudentList).toHaveBeenLastCalledWith(
      expect.objectContaining({
        sort_by: 'customer_email',
        sort_order: 'asc',
      })
    )
  })
})
