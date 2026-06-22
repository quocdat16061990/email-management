import { describe, test, expect, beforeAll, afterEach, afterAll } from 'vitest'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import {
  fetchStudentList,
  fetchStudentDetail,
  createStudent,
  updateStudent,
  deleteStudent,
  searchStudents,
} from './students'

const server = setupServer(
  http.get('/api/dashboard/', () => {
    return HttpResponse.json({
      students: [{ id: 1, full_name: 'Nguyen Van A', customer_email: 'a@example.com' }],
      pagination: { total_pages: 1, current_page: 1, total_items: 1 },
      operator_email: 'admin@example.com',
    })
  }),

  http.get('/api/students/1/', () => {
    return HttpResponse.json({
      id: 1,
      full_name: 'Nguyen Van A',
      customer_email: 'a@example.com',
      phone_number: '123456',
      status: 'ACTIVE',
    })
  }),

  http.post('/api/dashboard/create/', async ({ request }) => {
    const body = (await request.json()) as any
    return HttpResponse.json({ success: true, student: { id: 2, ...body } })
  }),

  http.put('/api/dashboard/1/', async ({ request }) => {
    const body = (await request.json()) as any
    return HttpResponse.json({ success: true, student: { id: 1, ...body } })
  }),

  http.delete('/api/dashboard/1/delete/', () => {
    return HttpResponse.json({ success: true, message: 'Deleted Student' })
  }),

  http.get('/courses/search-students/', () => {
    return HttpResponse.json({
      students: [{ id: 1, full_name: 'Nguyen Van A', email: 'a@example.com' }],
      pagination: { total_pages: 1, current_page: 1, total_items: 1 },
    })
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('api/students.ts', () => {
  test('fetchStudentList retrieves student list', async () => {
    const res = await fetchStudentList({ page: 1 })
    expect(res.students[0].full_name).toBe('Nguyen Van A')
    expect(res.operator_email).toBe('admin@example.com')
  })

  test('fetchStudentDetail retrieves student detail by ID', async () => {
    const res = await fetchStudentDetail(1)
    expect(res.full_name).toBe('Nguyen Van A')
    expect(res.status).toBe('ACTIVE')
  })

  test('createStudent makes post request to add student', async () => {
    const res = await createStudent({ customer_email: 'b@example.com', full_name: 'Tran Van B' })
    expect(res.success).toBe(true)
    expect(res.student.customer_email).toBe('b@example.com')
    expect(res.student.full_name).toBe('Tran Van B')
  })

  test('updateStudent makes put request to update student', async () => {
    const res = await updateStudent(1, { customer_email: 'a-new@example.com', full_name: 'Nguyen Van A Edited' })
    expect(res.success).toBe(true)
    expect(res.student.full_name).toBe('Nguyen Van A Edited')
  })

  test('deleteStudent makes delete request to remove student', async () => {
    const res = await deleteStudent(1)
    expect(res.success).toBe(true)
    expect(res.message).toBe('Deleted Student')
  })

  test('searchStudents searches for students within a course', async () => {
    const res = await searchStudents({ course_id: 1, q: 'Nguyen' })
    expect(res.students[0].full_name).toBe('Nguyen Van A')
  })
})
