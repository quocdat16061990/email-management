import { describe, test, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import CourseDetailPage from './CourseDetailPage'
import { useCourseDetail, useEnrollStudent } from '../hooks/useCourses'
import { useParams, BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<any>('react-router-dom')
  return {
    ...actual,
    useParams: vi.fn(),
  }
})

vi.mock('../hooks/useCourses', () => ({
  useCourseDetail: vi.fn(),
  useEnrollStudent: vi.fn(),
}))

vi.mock('../components/shared/Toast', () => ({
  showToast: vi.fn(),
}))

const queryClient = new QueryClient()

function renderCourseDetailPage() {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <CourseDetailPage />
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('pages/CourseDetailPage.tsx', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useParams).mockReturnValue({ id: '1' })

    vi.mocked(useCourseDetail).mockReturnValue({
      data: {
        course: { id: 1, name: 'Detail Course 101', description: 'Test course details description', web_link: 'http://testweb.org' },
        student_count: 7,
        students: [
          { name: 'Local Member A', email: 'localA@test.com', registration_date: '2026-05-23T04:30:20Z', expiry_date: '2027-05-23T04:30:20Z', status: 'ACTIVE' }
        ]
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any)

    vi.mocked(useEnrollStudent).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any)
  })

  test('renders loading spinner when data fetching is active', () => {
    vi.mocked(useCourseDetail).mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    } as any)

    const { container } = renderCourseDetailPage()
    expect(container.querySelector('.animate-spin')).toBeInTheDocument()
  })

  test('renders course header, statistics, and external website links', () => {
    renderCourseDetailPage()

    expect(screen.getByText('Detail Course 101')).toBeInTheDocument()
    expect(screen.getByText('Test course details description')).toBeInTheDocument()
    expect(screen.getByText('7 học viên')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Website Khóa Học/i })).toHaveAttribute('href', 'http://testweb.org')
  })

  test('renders student table showing registrations matching local records', () => {
    renderCourseDetailPage()

    expect(screen.getByText('Local Member A')).toBeInTheDocument()
    expect(screen.getByText('localA@test.com')).toBeInTheDocument()
  })
})
