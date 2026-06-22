import { apiDelete, apiGet, apiPost, apiPut } from './client'
import type { Pagination } from '../types/api'
import type { ChatGPTAccount, ChatGPTAccountInput } from '../types/chatgptAccount'

export interface ChatGPTAccountsResponse {
  accounts: ChatGPTAccount[]
  pagination: Pagination
}

export function fetchChatGPTAccounts(params: { q?: string; page?: number; all?: boolean }) {
  return apiGet<ChatGPTAccountsResponse>('/api/chatgpt-accounts/', {
    q: params.q,
    page: params.page,
    all: params.all ? 'true' : undefined,
  })
}

export function createChatGPTAccount(data: ChatGPTAccountInput) {
  return apiPost<{ success: boolean; account: ChatGPTAccount }>('/api/chatgpt-accounts/create/', data)
}

export function updateChatGPTAccount(id: number, data: ChatGPTAccountInput) {
  return apiPut<{ success: boolean; account: ChatGPTAccount }>(`/api/chatgpt-accounts/${id}/update/`, data)
}

export function deleteChatGPTAccount(id: number) {
  return apiDelete<{ success: boolean; message: string }>(`/api/chatgpt-accounts/${id}/delete/`)
}
