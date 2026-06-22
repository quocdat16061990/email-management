import { useEffect, useState } from 'react'
import { Settings, X } from 'lucide-react'
import { useStudentList, useUpdateCustomerChatGPTAccess } from '@/hooks/useStudents'
import { useDashboardStats } from '@/hooks/useAuth'
import { useChatGPTAccounts } from '@/hooks/useChatGPTAccounts'
import SearchInput from '@/components/shared/SearchInput'
import Pagination from '@/components/shared/Pagination'
import StatusBadge from '@/components/shared/StatusBadge'
import EmptyState from '@/components/shared/EmptyState'
import ErrorState from '@/components/shared/ErrorState'
import { showToast } from '@/components/shared/Toast'
import type { StudentListItem } from '@/types/student'

export default function DashboardPage() {
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('ALL')
  const [accessCustomer, setAccessCustomer] = useState<StudentListItem | null>(null)
  const [selectedAccountIds, setSelectedAccountIds] = useState<number[]>([])
  const { data, isLoading, isFetching, isError, refetch } = useStudentList({ q: query, page, status })
  const { data: stats } = useDashboardStats()
  const { data: accountData } = useChatGPTAccounts({ all: true })
  const accessMutation = useUpdateCustomerChatGPTAccess()

  useEffect(() => {
    if (accessCustomer) {
      setSelectedAccountIds(accessCustomer.allowed_chatgpt_account_ids || [])
    }
  }, [accessCustomer])

  const saveAccess = () => {
    if (!accessCustomer) return
    accessMutation.mutate(
      { id: accessCustomer.id, accountIds: selectedAccountIds },
      {
        onSuccess: () => {
          setAccessCustomer(null)
          showToast('success', 'Đã cập nhật quyền hiển thị ChatGPT cho khách hàng.')
        },
        onError: (error: Error) => showToast('error', error.message),
      },
    )
  }

  const toggleAccount = (id: number) => {
    setSelectedAccountIds((prev) => (
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    ))
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Tổng tài khoản ChatGPT', value: stats?.total_chatgpt_accounts ?? 0 },
          { label: 'Đang hoạt động', value: stats?.active_chatgpt_accounts ?? 0 },
          { label: 'Lỗi IMAP', value: stats?.imap_error_accounts ?? 0 },
          { label: 'Khách đã liên kết', value: stats?.linked_customers ?? 0 },
        ].map((stat) => (
          <div key={stat.label} className="bg-white rounded-lg border border-gray-100 shadow-sm p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{stat.label}</p>
            <p className="mt-1 text-2xl font-bold text-gray-900">{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
        <div className="w-full sm:w-80">
          <SearchInput
            value={query}
            onChange={(value) => {
              setQuery(value)
              setPage(1)
            }}
            placeholder="Tìm khách hàng Telegram..."
            loading={isFetching}
          />
        </div>
        <select
          value={status}
          onChange={(event) => {
            setStatus(event.target.value)
            setPage(1)
          }}
          className="px-3 py-2 rounded-lg border border-gray-200 bg-white text-sm font-medium text-gray-700"
        >
          <option value="ALL">Tất cả trạng thái</option>
          <option value="ACTIVE">Đang hoạt động</option>
          <option value="PENDING">Chờ xử lý</option>
          <option value="EXPIRED">Đã hết hạn</option>
        </select>
      </div>

      <div className="bg-white rounded-lg border border-gray-100 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Email</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Họ tên</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Telegram</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Quyền</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Hiển thị ChatGPT</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Hết hạn</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Trạng thái</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase">Thao tác</th>
              </tr>
            </thead>
            <tbody className={isFetching ? 'opacity-50' : ''}>
              {isLoading && (
                <tr><td colSpan={8} className="px-4 py-8 text-center text-sm text-gray-500">Đang tải dữ liệu...</td></tr>
              )}
              {isError && (
                <tr><td colSpan={8}><ErrorState onRetry={() => refetch()} /></td></tr>
              )}
              {data?.students.length === 0 && (
                <tr><td colSpan={8}><EmptyState text="Chưa có khách hàng nào." /></td></tr>
              )}
              {data?.students.map((customer) => {
                const customCount = customer.allowed_chatgpt_account_ids?.length || 0
                return (
                  <tr key={customer.id} className="border-b border-gray-50 last:border-0">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{customer.customer_email}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{customer.full_name || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {customer.is_verified_telegram ? customer.telegram_chat_id || 'Đã liên kết' : 'Chưa liên kết'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{customer.is_staff ? 'Nhân viên' : 'Khách hàng'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {customCount > 0 ? `Đã cấp: ${customCount} email` : 'Chưa cấp email'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{customer.expiry_date || '-'}</td>
                    <td className="px-4 py-3"><StatusBadge status={customer.status} /></td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => setAccessCustomer(customer)}
                        className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-brand-50 hover:text-brand-700"
                        title="Cấu hình email ChatGPT được hiển thị"
                      >
                        <Settings className="h-4 w-4" />
                        Cấu hình
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        {data?.pagination && (
          <div className="px-4 py-3 border-t border-gray-100">
            <Pagination pagination={data.pagination} onPageChange={setPage} />
          </div>
        )}
      </div>

      {accessCustomer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4">
          <div className="w-full max-w-2xl rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-100 px-5 py-4">
              <div>
                <h2 className="text-base font-semibold text-gray-900">Cấu hình hiển thị ChatGPT</h2>
                <p className="mt-1 text-xs text-gray-500">{accessCustomer.customer_email}</p>
              </div>
              <button className="rounded-lg p-2 text-gray-500 hover:bg-gray-100" onClick={() => setAccessCustomer(null)}>
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="p-5 space-y-4">
              <div className="rounded-lg border border-amber-100 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                Chọn các email ChatGPT mà khách hàng này được phép thấy trên Telegram. Nếu không chọn email nào, khách sẽ không thấy tài khoản ChatGPT nào để lấy OTP.
              </div>
              <div className="max-h-80 overflow-y-auto rounded-lg border border-gray-100">
                {accountData?.accounts.map((account) => (
                  <label key={account.id} className="flex items-center gap-3 border-b border-gray-50 px-4 py-3 last:border-0 hover:bg-gray-50">
                    <input
                      type="checkbox"
                      checked={selectedAccountIds.includes(account.id)}
                      onChange={() => toggleAccount(account.id)}
                      className="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                    />
                    <span className="flex-1 text-sm font-medium text-gray-900">{account.email}</span>
                    <span className="text-xs text-gray-500">
                      {account.status === 'ACTIVE' ? 'Đang hoạt động' : 'Không hoạt động'}
                    </span>
                  </label>
                ))}
                {accountData?.accounts.length === 0 && <EmptyState text="Chưa có tài khoản ChatGPT nào." />}
              </div>
            </div>
            <div className="flex justify-between gap-2 border-t border-gray-100 px-5 py-4">
              <button
                className="rounded-lg px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100"
                onClick={() => setSelectedAccountIds([])}
              >
                Bỏ chọn tất cả
              </button>
              <div className="flex gap-2">
                <button className="rounded-lg px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100" onClick={() => setAccessCustomer(null)}>Hủy</button>
                <button
                  className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
                  disabled={accessMutation.isPending}
                  onClick={saveAccess}
                >
                  {accessMutation.isPending ? 'Đang lưu...' : 'Lưu cấu hình'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
