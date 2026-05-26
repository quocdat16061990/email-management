import axios, { AxiosError } from 'axios'

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message)
    this.name = 'ApiError'
  }
}

const BASE = ''

const api = axios.create({
  baseURL: BASE,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Convert Axios errors to our standard ApiError for backward compatibility
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ error?: string }>) => {
    const status = error.response?.status || 500
    const msg = error.response?.data?.error || `HTTP ${status}`
    return Promise.reject(new ApiError(msg, status))
  }
)

export async function apiFetch<T>(endpoint: string, options: any = {}): Promise<T> {
  const response = await api({
    url: endpoint,
    method: options.method || 'GET',
    data: options.body ? JSON.parse(options.body) : undefined,
    headers: options.headers,
  })
  return response.data
}

export async function apiGet<T>(endpoint: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const response = await api.get<T>(endpoint, { params })
  return response.data
}

export async function apiPost<T>(endpoint: string, body: unknown): Promise<T> {
  const response = await api.post<T>(endpoint, body)
  return response.data
}

export async function apiPut<T>(endpoint: string, body: unknown): Promise<T> {
  const response = await api.put<T>(endpoint, body)
  return response.data
}

export async function apiDelete<T>(endpoint: string): Promise<T> {
  const response = await api.delete<T>(endpoint)
  return response.data
}

export async function apiGetBlob(endpoint: string, params?: Record<string, string | number | undefined>): Promise<Blob> {
  const response = await api.get<Blob>(endpoint, { params, responseType: 'blob' })
  return response.data
}
