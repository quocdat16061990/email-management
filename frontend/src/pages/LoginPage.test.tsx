import { describe, test, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LoginPage from './LoginPage'
import { useAuth } from '../context/AuthContext'
import { useLogin } from '../hooks/useAuth'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

vi.mock('../hooks/useAuth', () => ({
  useLogin: vi.fn(),
}))

vi.mock('../components/shared/Toast', () => ({
  showToast: vi.fn(),
}))

function renderLoginPage() {
  const queryClient = new QueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    </QueryClientProvider>,
  )
}

describe('pages/LoginPage.tsx', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      operatorEmail: '',
      checkAuth: vi.fn(),
    })

    vi.mocked(useLogin).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any)
  })

  test('renders form elements correctly', () => {
    renderLoginPage()

    expect(screen.getByRole('heading', { name: /Anh Lập Trình/i })).toBeInTheDocument()
    expect(screen.getByText('Email')).toBeInTheDocument()
    expect(screen.getByText('Mật khẩu')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('admin@example.com')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Đăng nhập vào hệ thống/i })).toBeInTheDocument()
  })

  test('shows spinner if authentication check is loading', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
      operatorEmail: '',
      checkAuth: vi.fn(),
    })

    const { container } = renderLoginPage()

    const spinner = container.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
  })

  test('displays validation errors when fields are submitted empty', async () => {
    const { container } = renderLoginPage()

    const form = container.querySelector('form')!
    fireEvent.submit(form)

    expect(await screen.findByText('Email không được để trống')).toBeInTheDocument()
    expect(await screen.findByText('Mật khẩu không được để trống')).toBeInTheDocument()
  })

  test('displays email validation error when email format is invalid', async () => {
    const { container } = renderLoginPage()
    const user = userEvent.setup()

    const emailInput = screen.getByPlaceholderText('admin@example.com')
    await user.type(emailInput, 'invalid-email')

    const form = container.querySelector('form')!
    fireEvent.submit(form)

    expect(await screen.findByText('Email không hợp lệ')).toBeInTheDocument()
  })

  test('submits form with trimmed email and password when inputs are valid', async () => {
    const mockMutate = vi.fn()
    vi.mocked(useLogin).mockReturnValue({
      mutate: mockMutate,
      isPending: false,
    } as any)

    const { container } = renderLoginPage()
    const user = userEvent.setup()

    const emailInput = screen.getByPlaceholderText('admin@example.com')
    const passwordInput = screen.getByPlaceholderText('••••••••')

    await user.type(emailInput, '  admin@example.com  ')
    await user.type(passwordInput, 'secretpassword')

    const form = container.querySelector('form')!
    fireEvent.submit(form)

    await waitFor(() => {
      expect(mockMutate).toHaveBeenCalledWith(
        { email: 'admin@example.com', password: 'secretpassword' },
        expect.any(Object),
      )
    })
  })
})
