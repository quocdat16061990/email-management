export type ChatGPTAccountStatus = 'ACTIVE' | 'INACTIVE' | 'ERROR'

export interface ChatGPTAccount {
  id: number
  email: string
  password: string
  imap_host: string
  imap_port: number
  imap_user: string
  imap_password: string
  status: ChatGPTAccountStatus
  created_at: string
  updated_at: string
}

export interface ChatGPTAccountInput {
  email: string
  password: string
  imap_host: string
  imap_port: number
  imap_user?: string
  imap_password: string
  status: ChatGPTAccountStatus
}
