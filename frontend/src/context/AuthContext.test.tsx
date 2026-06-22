import { describe, test, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AuthProvider, useAuth } from './AuthContext'
import { fetchDashboardStats } from '../api/auth'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Mock the API function
vi.mock('../api/auth', () => ({
  fetchDashboardStats: vi.fn(),
}))

function TestComponent() {
  const { isAuthenticated, isLoading, checkAuth } = useAuth()
  return (
    <div>
      <span data-testid="auth-state">{isAuthenticated ? 'authenticated' : 'unauthenticated'}</span>
      <span data-testid="loading-state">{isLoading ? 'loading' : 'ready'}</span>
      <button data-testid="check-btn" onClick={checkAuth}>Check Auth</button>
    </div>
  )
}

function renderWithQuery(ui: React.ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
      },
    },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  )
}

describe('context/AuthContext.tsx', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  test('sets isAuthenticated to true when fetchDashboardStats succeeds', async () => {
    // Mock success response
    vi.mocked(fetchDashboardStats).mockResolvedValue({
      total_students: 100,
      active_count: 80,
      pending_count: 0,
      expired_count: 20,
      total_courses: 5,
    })

    renderWithQuery(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    // Wait for useQuery to resolve
    await screen.findByText('ready')
    expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
    expect(fetchDashboardStats).toHaveBeenCalledTimes(1)
  })

  test('sets isAuthenticated to false when fetchDashboardStats fails', async () => {
    // Mock failure response
    vi.mocked(fetchDashboardStats).mockRejectedValue(new Error('Unauthorized'))

    renderWithQuery(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await screen.findByText('ready')
    expect(screen.getByTestId('auth-state')).toHaveTextContent('unauthenticated')
    expect(fetchDashboardStats).toHaveBeenCalledTimes(1)
  })
})
