import { describe, test, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import CoursesPage from './CoursesPage'
import { useCourseList, useDeleteCourse, useUpdateWebsite } from '../hooks/useCourses'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../hooks/useCourses', () => ({
  useCourseList: vi.fn(),
  useDeleteCourse: vi.fn(),
  useUpdateWebsite: vi.fn(),
}))

vi.mock('../components/shared/Toast', () => ({
  showToast: vi.fn(),
}))

const queryClient = new QueryClient()

function renderCoursesPage() {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <CoursesPage />
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('pages/CoursesPage.tsx', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(useCourseList).mockReturnValue({
      data: {
        courses: [
          { id: 1, name: 'Test Course 101', web_link: 'http://example.com', student_count: 12, created_at: '2026-05-23T04:30:20Z' }
        ],
        pagination: { total_pages: 1, current_page: 1, total_items: 1 }
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any)

    vi.mocked(useDeleteCourse).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any)

    vi.mocked(useUpdateWebsite).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any)
  })

  test('renders page headings and main controls', () => {
    renderCoursesPage()

    expect(screen.getByText('Danh sách khóa học')).toBeInTheDocument()
    expect(screen.getByText('Quản lý các chương trình học tập đang hoạt động.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /\+ Thêm khóa học/i })).toBeInTheDocument()
  })

  test('renders course list items', () => {
    renderCoursesPage()

    expect(screen.getByText('Test Course 101')).toBeInTheDocument()
    expect(screen.getByText('12 học viên')).toBeInTheDocument()
  })

  test('renders empty state when there are no courses', () => {
    vi.mocked(useCourseList).mockReturnValue({
      data: { courses: [], pagination: null },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any)

    renderCoursesPage()

    expect(screen.getByText('Chưa có khóa học nào.')).toBeInTheDocument()
  })

  test('calls useCourseList with correct sort params when header is clicked', async () => {
    const user = userEvent.setup()
    renderCoursesPage()

    const nameHeader = screen.getByRole('columnheader', { name: /Khóa học/i })
    await user.click(nameHeader)

    expect(useCourseList).toHaveBeenLastCalledWith(
      expect.objectContaining({
        sort_by: 'name',
        sort_order: 'asc',
      })
    )
  })
})
