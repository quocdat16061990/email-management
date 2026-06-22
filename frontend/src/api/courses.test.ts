import { describe, test, expect, beforeAll, afterEach, afterAll } from 'vitest'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import {
  fetchCourseList,
  fetchCourseDetail,
  createCourse,
  updateCourse,
  deleteCourse,
  enrollStudent,
  updateCourseWebsite,
} from './courses'

const server = setupServer(
  http.get('/api/courses/', () => {
    return HttpResponse.json({
      courses: [{ id: 1, name: 'React Test', student_count: 5 }],
      pagination: {
        total_pages: 1,
        current_page: 1,
        total_count: 1,
        has_next: false,
        has_prev: false,
        next_page_number: null,
        prev_page_number: null
      },
    })
  }),

  http.get('/api/courses/1/', () => {
    return HttpResponse.json({
      course: { id: 1, name: 'React Test' },
      student_count: 5,
      students: [],
    })
  }),

  http.post('/api/courses/create/', async ({ request }) => {
    const body = (await request.json()) as any
    return HttpResponse.json({ success: true, course: { id: 2, ...body } })
  }),

  http.put('/api/courses/1/update/', async ({ request }) => {
    const body = (await request.json()) as any
    return HttpResponse.json({ success: true, course: { id: 1, ...body } })
  }),

  http.delete('/api/courses/1/delete/', () => {
    return HttpResponse.json({ success: true, message: 'Deleted' })
  }),


  http.post('/api/enroll/', async ({ request }) => {
    const body = (await request.json()) as any
    return HttpResponse.json({
      success: true,
      enrollment: {
        id: 99,
        course_id: body.course_id,
        customer_id: body.student_id || 123,
        registration_date: '',
        expiry_date: '',
        status: 'ACTIVE',
        created: true
      },
    })
  }),

  http.post('/courses/update-website/', async ({ request }) => {
    const body = (await request.json()) as any
    return HttpResponse.json({ success: true, web_link: body.web_link })
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('api/courses.ts', () => {
  test('fetchCourseList retrieves course items', async () => {
    const res = await fetchCourseList({ page: 1 })
    expect(res.courses[0].name).toBe('React Test')
    expect(res.pagination.total_count).toBe(1)
  })

  test('fetchCourseDetail retrieves course detail by ID', async () => {
    const res = await fetchCourseDetail(1)
    expect(res.course.name).toBe('React Test')
    expect(res.student_count).toBe(5)
  })

  test('createCourse makes a post request to create new course', async () => {
    const res = await createCourse({ name: 'Vue Test' })
    expect(res.success).toBe(true)
    expect(res.course.id).toBe(2)
    expect(res.course.name).toBe('Vue Test')
  })

  test('updateCourse makes a put request to modify existing course', async () => {
    const res = await updateCourse(1, { name: 'React Test Updated' })
    expect(res.success).toBe(true)
    expect(res.course.name).toBe('React Test Updated')
  })

  test('deleteCourse sends delete request to remove course', async () => {
    const res = await deleteCourse(1)
    expect(res.success).toBe(true)
    expect(res.message).toBe('Deleted')
  })


  test('enrollStudent sends enrollment request', async () => {
    const res = await enrollStudent({ course_id: 1, student_id: 456 })
    expect(res.success).toBe(true)
    expect(res.enrollment.customer_id).toBe(456)
  })

  test('updateCourseWebsite updates course web link', async () => {
    const res = await updateCourseWebsite({ id: 1, web_link: 'http://vue.org' })
    expect(res.success).toBe(true)
    expect(res.web_link).toBe('http://vue.org')
  })
})
