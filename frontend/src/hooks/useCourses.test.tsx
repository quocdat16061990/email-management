import { describe, test, expect, beforeAll, afterEach, afterAll } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import {
  useCourseList,
  useCourseDetail,
  useCreateCourse,
  useUpdateCourse,
  useDeleteCourse,
} from './useCourses'

const server = setupServer(
  http.get('/api/courses/', () => {
    return HttpResponse.json({
      courses: [{ id: 1, name: 'Query Course' }],
      pagination: { total_pages: 1, current_page: 1, total_items: 1 },
    })
  }),

  http.get('/api/courses/1/', () => {
    return HttpResponse.json({
      course: { id: 1, name: 'Query Course' },
      student_count: 3,
      students: [],
    })
  }),

  http.post('/api/courses/create/', async ({ request }) => {
    const body = (await request.json()) as any
    return HttpResponse.json({ success: true, course: { id: 3, ...body } })
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('hooks/useCourses.ts', () => {
  test('useCourseList fetches course list successfully', async () => {
    const { result } = renderHook(() => useCourseList({ page: 1 }), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.courses[0].name).toBe('Query Course')
  })

  test('useCourseDetail fetches course details successfully when ID is provided', async () => {
    const { result } = renderHook(() => useCourseDetail(1), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.course.name).toBe('Query Course')
    expect(result.current.data?.student_count).toBe(3)
  })

  test('useCreateCourse creates course successfully', async () => {
    const { result } = renderHook(() => useCreateCourse(), {
      wrapper: createWrapper(),
    })

    await result.current.mutateAsync({ name: 'New Hook Course' })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.course.id).toBe(3)
    expect(result.current.data?.course.name).toBe('New Hook Course')
  })
})
