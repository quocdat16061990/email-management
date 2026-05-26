import { apiGet, apiPost, apiPut, apiDelete, apiGetBlob } from './client'
import type { Course, CourseLink, VoomlyStudent } from '../types/course'
import type { Pagination } from '../types/api'
import type { Enrollment } from '../types/enrollment'

export interface CourseListResponse {
  courses: Course[]
  pagination: Pagination
}

export function fetchCourseList(params: { page?: number; sort_by?: string; sort_order?: 'asc' | 'desc'; all?: boolean }): Promise<CourseListResponse> {
  return apiGet<CourseListResponse>('/api/courses/', params as Record<string, string | number | undefined>)
}

export function exportCourses(params?: {
  course_ids?: string
  q?: string
}): Promise<Blob> {
  return apiGetBlob('/api/courses/export/', params as Record<string, string | number | undefined>)
}

export interface CourseDetailResponse {
  course: Course
  student_count: number
  voomly_students: VoomlyStudent[]
  voomly_error?: string
}

export function fetchCourseDetail(id: number): Promise<CourseDetailResponse> {
  return apiGet<CourseDetailResponse>(`/api/courses/${id}/`)
}

export interface CreateCourseInput {
  name: string
  spotlight_id?: string
  description?: string
  web_link?: string
  links?: CourseLink[]
}

export function createCourse(data: CreateCourseInput): Promise<{ success: boolean; course: Course }> {
  return apiPost('/api/courses/create/', data)
}

export function updateCourse(id: number, data: CreateCourseInput): Promise<{ success: boolean; course: Course }> {
  return apiPut(`/api/courses/${id}/update/`, data)
}

export function deleteCourse(id: number): Promise<{ success: boolean; message: string }> {
  return apiDelete(`/api/courses/${id}/delete/`)
}

export function syncCourses(): Promise<{ success: boolean; result: { total: number; created: number; updated: number } }> {
  return apiPost('/api/sync/courses/', {})
}

export interface EnrollStudentInput {
  course_id: number
  student_id?: number
  customer_email?: string
  full_name?: string
  phone_number?: string
  registration_date?: string
  expiry_date?: string
  status?: string
}

export function enrollStudent(data: EnrollStudentInput): Promise<{ success: boolean; enrollment: Enrollment; voomly_synced: boolean }> {
  return apiPost('/api/enroll/', data)
}

export function updateCourseWebsite(data: { id: number; web_link: string }): Promise<{ success: boolean; web_link: string; message?: string }> {
  return apiPost('/courses/update-website/', data)
}
