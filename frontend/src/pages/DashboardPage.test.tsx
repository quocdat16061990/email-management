import { describe, test, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DashboardPage from './DashboardPage'
import { useStudentList, useUpdateCustomerChatGPTAccess } from '../hooks/useStudents'
import { useChatGPTAccounts } from '../hooks/useChatGPTAccounts'
import { fetchDashboardStats } from '../api/auth'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../hooks/useStudents', () => ({
  useStudentList: vi.fn(),
  useUpdateCustomerChatGPTAccess: vi.fn(),
}))

vi.mock('../hooks/useChatGPTAccounts', () => ({
  useChatGPTAccounts: vi.fn(),
}))

vi.mock('../api/auth', () => ({
  fetchDashboardStats: vi.fn(),
}))

vi.mock('../components/shared/Toast', () => ({
  showToast: vi.fn(),
}))

function renderDashboardPage() {
  const queryClient = new QueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    </QueryClientProvider>,
  )
}

describe('pages/DashboardPage.tsx', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(useStudentList).mockReturnValue({
      data: {
        students: [
          {
            id: 1,
            full_name: 'Nguyễn Văn A',
            customer_email: 'test@example.com',
            phone_number: '123456789',
            status: 'ACTIVE',
            expiry_date: '2026-12-31',
            telegram_chat_id: 12345,
            is_verified_telegram: true,
            is_staff: false,
            allowed_chatgpt_account_ids: [1],
          },
        ],
        pagination: {
          total_pages: 1,
          current_page: 1,
          has_prev: false,
          has_next: false,
          total_count: 1,
        },
      },
      isLoading: false,
      isFetching: false,
      isError: false,
      refetch: vi.fn(),
    } as any)

    vi.mocked(useChatGPTAccounts).mockReturnValue({
      data: {
        accounts: [
          {
            id: 1,
            email: 'chatgpt@example.com',
            password: 'secret',
            imap_host: 'imap.gmail.com',
            imap_port: 993,
            imap_user: '',
            imap_password: 'imap-secret',
            status: 'ACTIVE',
            created_at: '',
            updated_at: '',
          },
        ],
        pagination: {
          total_pages: 1,
          current_page: 1,
          has_prev: false,
          has_next: false,
          total_count: 1,
        },
      },
    } as any)

    vi.mocked(useUpdateCustomerChatGPTAccess).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any)

    vi.mocked(fetchDashboardStats).mockResolvedValue({
      total_chatgpt_accounts: 10,
      active_chatgpt_accounts: 8,
      imap_error_accounts: 1,
      linked_customers: 7,
    } as any)
  })

  test('renders stats cards and main controls', async () => {
    renderDashboardPage()

    expect(screen.getByText('Tổng tài khoản ChatGPT')).toBeInTheDocument()
    expect(screen.getAllByText('Đang hoạt động')[0]).toBeInTheDocument()
    expect(screen.getByText('Lỗi IMAP')).toBeInTheDocument()
    expect(screen.getByText('Khách đã liên kết')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Tìm khách hàng Telegram...')).toBeInTheDocument()
  })

  test('renders customer list table successfully', () => {
    renderDashboardPage()

    expect(screen.getByText('Nguyễn Văn A')).toBeInTheDocument()
    expect(screen.getByText('test@example.com')).toBeInTheDocument()
    expect(screen.getByText('Đã cấp: 1 email')).toBeInTheDocument()
  })

  test('renders loading state when loading customers', () => {
    vi.mocked(useStudentList).mockReturnValue({
      data: null,
      isLoading: true,
      isFetching: false,
      isError: false,
      refetch: vi.fn(),
    } as any)

    renderDashboardPage()

    expect(screen.getByText('Đang tải dữ liệu...')).toBeInTheDocument()
  })

  test('renders empty state when there are no customers', () => {
    vi.mocked(useStudentList).mockReturnValue({
      data: { students: [], pagination: null },
      isLoading: false,
      isFetching: false,
      isError: false,
      refetch: vi.fn(),
    } as any)

    renderDashboardPage()

    expect(screen.getByText('Chưa có khách hàng nào.')).toBeInTheDocument()
  })

  test('opens ChatGPT access configuration modal', async () => {
    const user = userEvent.setup()
    renderDashboardPage()

    await user.click(screen.getByRole('button', { name: /Cấu hình/i }))

    expect(screen.getByText('Cấu hình hiển thị ChatGPT')).toBeInTheDocument()
    expect(screen.getByText('chatgpt@example.com')).toBeInTheDocument()
  })
})
