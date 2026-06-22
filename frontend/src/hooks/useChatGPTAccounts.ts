import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createChatGPTAccount,
  deleteChatGPTAccount,
  fetchChatGPTAccounts,
  updateChatGPTAccount,
} from '../api/chatgptAccounts'
import type { ChatGPTAccountInput } from '../types/chatgptAccount'

export function useChatGPTAccounts(params: { q?: string; page?: number; all?: boolean }) {
  return useQuery({
    queryKey: ['chatgpt-accounts', params],
    queryFn: () => fetchChatGPTAccounts(params),
    placeholderData: keepPreviousData,
  })
}

export function useCreateChatGPTAccount() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ChatGPTAccountInput) => createChatGPTAccount(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['chatgpt-accounts'] })
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] })
    },
  })
}

export function useUpdateChatGPTAccount() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ChatGPTAccountInput }) => updateChatGPTAccount(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['chatgpt-accounts'] })
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] })
    },
  })
}

export function useDeleteChatGPTAccount() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteChatGPTAccount(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['chatgpt-accounts'] })
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] })
    },
  })
}
