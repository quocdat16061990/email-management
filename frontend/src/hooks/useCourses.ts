import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import {
  fetchCourseList,
  fetchCourseDetail,
  exportCourses,
  createCourse,
  updateCourse,
  deleteCourse,
  syncCourses,
  enrollStudent,
  updateCourseWebsite,
  type CreateCourseInput,
  type EnrollStudentInput,
} from '../api/courses'

export function useCourseList(params: { page?: number; sort_by?: string; sort_order?: 'asc' | 'desc'; all?: boolean }) {
  return useQuery({
    queryKey: ['courses', params],
    queryFn: () => fetchCourseList(params),
    placeholderData: keepPreviousData,
  })
}

export function useCourseDetail(id: number | null) {
  return useQuery({
    queryKey: ['course', id],
    queryFn: () => fetchCourseDetail(id!),
    enabled: !!id,
  })
}

export function useExportCourses() {
  return useMutation({
    mutationFn: (params?: { course_ids?: string; q?: string }) => exportCourses(params),
  })
}

export function useCreateCourse() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateCourseInput) => createCourse(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['courses'] }),
  })
}

export function useUpdateCourse() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: CreateCourseInput }) => updateCourse(id, data),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ['courses'] })
      qc.invalidateQueries({ queryKey: ['course', id] })
    },
  })
}

export function useDeleteCourse() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteCourse(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['courses'] }),
  })
}

export function useSyncCourses() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => syncCourses(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['courses'] }),
  })
}

export function useEnrollStudent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: EnrollStudentInput) => enrollStudent(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['course'] })
      qc.invalidateQueries({ queryKey: ['student-search'] })
      qc.invalidateQueries({ queryKey: ['students'] })
    },
  })
}

export function useUpdateWebsite() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { id: number; web_link: string }) => updateCourseWebsite(data),
    onSuccess: (_, { id }) => qc.invalidateQueries({ queryKey: ['course', id] }),
  })
}
