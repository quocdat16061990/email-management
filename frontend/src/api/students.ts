import { apiGet, apiPost, apiPut, apiDelete, apiGetBlob } from './client'
import type { StudentListItem, Student, StudentSearchResult } from '../types/student'
import type { Pagination } from '../types/api'

export interface StudentListResponse {
  students: StudentListItem[]
  pagination: Pagination
  operator_email: string
}

export function fetchStudentList(params: {
  q?: string
  page?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  course_ids?: string
  status?: string
}): Promise<StudentListResponse> {
  return apiGet<StudentListResponse>('/api/dashboard/', params as Record<string, string | number | undefined>)
}

export function exportStudents(params: {
  student_ids?: string
  course_ids?: string
  status?: string
  q?: string
  export_type: 'simple' | 'full'
}): Promise<Blob> {
  return apiGetBlob('/api/students/export/', params as Record<string, string | number | undefined>)
}

export function fetchStudentDetail(id: number): Promise<Student> {
  return apiGet<Student>(`/api/students/${id}/`)
}

export interface CreateStudentInput {
  customer_email: string
  full_name?: string
  phone_number?: string
  enrollments?: {
    course_id: number
    registration_date?: string
    expiry_date?: string
    status?: string
  }[]
}

export function createStudent(data: CreateStudentInput): Promise<{ success: boolean; student: Student }> {
  return apiPost('/api/dashboard/create/', data)
}

export function updateStudent(id: number, data: CreateStudentInput): Promise<{ success: boolean; student: Student }> {
  return apiPut(`/api/dashboard/${id}/`, data)
}

export function deleteStudent(id: number): Promise<{ success: boolean; message: string }> {
  return apiDelete(`/api/dashboard/${id}/delete/`)
}

export function updateCustomerChatGPTAccess(id: number, accountIds: number[]): Promise<{ success: boolean; student: Student }> {
  return apiPut(`/api/customers/${id}/chatgpt-access/`, { account_ids: accountIds })
}

export interface StudentSearchResponse {
  students: StudentSearchResult[]
  pagination: Pagination
}

export function searchStudents(params: { course_id?: number; q?: string; page?: number }): Promise<StudentSearchResponse> {
  return apiGet<StudentSearchResponse>('/courses/search-students/', params as Record<string, string | number | undefined>)
}
