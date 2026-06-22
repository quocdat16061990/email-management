import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import {
  fetchStudentList,
  fetchStudentDetail,
  createStudent,
  updateStudent,
  deleteStudent,
  searchStudents,
  exportStudents,
  type CreateStudentInput,
} from '../api/students'
import type { StudentSearchResult } from '../types/student'
import type { Pagination } from '../types/api'

export function useStudentList(params: {
  q?: string
  page?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  course_ids?: string
  status?: string
}) {
  return useQuery({
    queryKey: ['students', params],
    queryFn: () => fetchStudentList(params),
    placeholderData: keepPreviousData,
  })
}

export function useStudentDetail(id: number | null) {
  return useQuery({
    queryKey: ['student', id],
    queryFn: () => fetchStudentDetail(id!),
    enabled: !!id,
  })
}

export function useStudentSearch(params: { course_id?: number; q?: string; page?: number }) {
  return useQuery({
    queryKey: ['student-search', params],
    queryFn: () => searchStudents(params),
    enabled: !!params.course_id,
  })
}

export function useCreateStudent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateStudentInput) => createStudent(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['students'] })
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] })
    },
  })
}

export function useUpdateStudent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: CreateStudentInput }) => updateStudent(id, data),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ['students'] })
      qc.invalidateQueries({ queryKey: ['student', id] })
    },
  })
}

export function useDeleteStudent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteStudent(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['students'] })
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] })
    },
  })
}

export function useExportStudents() {
  return useMutation({
    mutationFn: (params: {
      student_ids?: string
      course_ids?: string
      status?: string
      q?: string
      export_type: 'simple' | 'full'
    }) => exportStudents(params),
  })
}
