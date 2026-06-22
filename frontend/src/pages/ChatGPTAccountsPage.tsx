import { useMemo, useState } from 'react'
import { Pencil, Plus, Trash2, X } from 'lucide-react'
import SearchInput from '@/components/shared/SearchInput'
import Pagination from '@/components/shared/Pagination'
import EmptyState from '@/components/shared/EmptyState'
import ErrorState from '@/components/shared/ErrorState'
import { showToast } from '@/components/shared/Toast'
import {
  useChatGPTAccounts,
  useCreateChatGPTAccount,
  useDeleteChatGPTAccount,
  useUpdateChatGPTAccount,
} from '@/hooks/useChatGPTAccounts'
import type { ChatGPTAccount, ChatGPTAccountInput, ChatGPTAccountStatus } from '@/types/chatgptAccount'

const emptyForm: ChatGPTAccountInput = {
  email: '',
  password: '',
  imap_host: 'imap.gmail.com',
  imap_port: 993,
  imap_user: '',
  imap_password: '',
  status: 'ACTIVE',
}

function statusLabel(status: ChatGPTAccountStatus) {
  if (status === 'ACTIVE') return 'Đang hoạt động'
  if (status === 'ERROR') return 'Lỗi IMAP'
  return 'Tạm dừng'
}

export default function ChatGPTAccountsPage() {
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const [editing, setEditing] = useState<ChatGPTAccount | null>(null)
  const [form, setForm] = useState<ChatGPTAccountInput>(emptyForm)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const { data, isLoading, isFetching, isError, refetch } = useChatGPTAccounts({ q: query, page })
  const createMutation = useCreateChatGPTAccount()
  const updateMutation = useUpdateChatGPTAccount()
  const deleteMutation = useDeleteChatGPTAccount()

  const isSaving = createMutation.isPending || updateMutation.isPending
  const modalTitle = useMemo(() => (editing ? 'Sửa tài khoản ChatGPT' : 'Thêm tài khoản ChatGPT'), [editing])

  const openCreate = () => {
    setEditing(null)
    setForm(emptyForm)
    setIsFormOpen(true)
  }

  const openEdit = (account: ChatGPTAccount) => {
    setEditing(account)
    setForm({
      email: account.email,
      password: account.password,
      imap_host: account.imap_host,
      imap_port: account.imap_port,
      imap_user: account.imap_user,
      imap_password: account.imap_password,
      status: account.status,
    })
    setIsFormOpen(true)
  }

  const save = () => {
    const mutation = editing
      ? updateMutation.mutate.bind(updateMutation, { id: editing.id, data: form })
      : createMutation.mutate.bind(createMutation, form)
    mutation({
      onSuccess: () => {
        setIsFormOpen(false)
        showToast('success', editing ? 'Đã cập nhật tài khoản.' : 'Đã thêm tài khoản.')
      },
      onError: (error: Error) => showToast('error', error.message),
    })
  }

  const remove = (account: ChatGPTAccount) => {
    if (!window.confirm(`Xóa tài khoản ChatGPT "${account.email}"?`)) return
    deleteMutation.mutate(account.id, {
      onSuccess: () => showToast('success', 'Đã xóa tài khoản.'),
      onError: (error: Error) => showToast('error', error.message),
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="w-full sm:w-80">
          <SearchInput
            value={query}
            onChange={(value) => {
              setQuery(value)
              setPage(1)
            }}
            placeholder="Tìm email ChatGPT..."
            loading={isFetching}
          />
        </div>
        <button
          type="button"
          onClick={openCreate}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
        >
          <Plus className="h-4 w-4" />
          Thêm tài khoản
        </button>
      </div>

      <div className="bg-white rounded-lg border border-gray-100 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Email</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Trạng thái</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase">IMAP Server</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase">Hành động</th>
              </tr>
            </thead>
            <tbody className={isFetching ? 'opacity-50' : ''}>
              {isLoading && (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-sm text-gray-500">Đang tải dữ liệu...</td></tr>
              )}
              {isError && (
                <tr><td colSpan={4}><ErrorState onRetry={() => refetch()} /></td></tr>
              )}
              {data?.accounts.length === 0 && (
                <tr><td colSpan={4}><EmptyState text="Chưa có tài khoản ChatGPT nào." /></td></tr>
              )}
              {data?.accounts.map((account) => (
                <tr key={account.id} className="border-b border-gray-50 last:border-0">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{account.email}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{statusLabel(account.status)}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{account.imap_host}:{account.imap_port}</td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      <button className="rounded-lg p-2 text-gray-500 hover:bg-gray-100" onClick={() => openEdit(account)} title="Sửa">
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button className="rounded-lg p-2 text-gray-500 hover:bg-red-50 hover:text-red-600" onClick={() => remove(account)} title="Xóa">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {data?.pagination && (
          <div className="px-4 py-3 border-t border-gray-100">
            <Pagination pagination={data.pagination} onPageChange={setPage} />
          </div>
        )}
      </div>

      {isFormOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4">
          <div className="w-full max-w-2xl rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-100 px-5 py-4">
              <h2 className="text-base font-semibold text-gray-900">{modalTitle}</h2>
              <button className="rounded-lg p-2 text-gray-500 hover:bg-gray-100" onClick={() => setIsFormOpen(false)}>
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="grid gap-4 p-5 sm:grid-cols-2">
              <input className="rounded-lg border border-gray-200 px-3 py-2 text-sm" placeholder="Email ChatGPT" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              <input className="rounded-lg border border-gray-200 px-3 py-2 text-sm" placeholder="Mật khẩu đăng nhập" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
              <input className="rounded-lg border border-gray-200 px-3 py-2 text-sm" placeholder="IMAP Server" value={form.imap_host} onChange={(e) => setForm({ ...form, imap_host: e.target.value })} />
              <input className="rounded-lg border border-gray-200 px-3 py-2 text-sm" type="number" placeholder="IMAP Port" value={form.imap_port} onChange={(e) => setForm({ ...form, imap_port: Number(e.target.value) })} />
              <input className="rounded-lg border border-gray-200 px-3 py-2 text-sm" placeholder="IMAP Username" value={form.imap_user} onChange={(e) => setForm({ ...form, imap_user: e.target.value })} />
              <input className="rounded-lg border border-gray-200 px-3 py-2 text-sm" placeholder="Mật khẩu ứng dụng email" value={form.imap_password} onChange={(e) => setForm({ ...form, imap_password: e.target.value })} />
              <select className="rounded-lg border border-gray-200 px-3 py-2 text-sm sm:col-span-2" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value as ChatGPTAccountStatus })}>
                <option value="ACTIVE">Đang hoạt động</option>
                <option value="INACTIVE">Tạm dừng</option>
                <option value="ERROR">Lỗi IMAP</option>
              </select>
            </div>
            <div className="flex justify-end gap-2 border-t border-gray-100 px-5 py-4">
              <button className="rounded-lg px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100" onClick={() => setIsFormOpen(false)}>Hủy</button>
              <button className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60" disabled={isSaving} onClick={save}>
                {isSaving ? 'Đang lưu...' : 'Lưu'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
