import { cn } from '../../lib/utils'
import type { Pagination as PaginationType } from '../../types/api'

interface PaginationProps {
  pagination: PaginationType
  onPageChange: (page: number) => void
}

export default function Pagination({ pagination, onPageChange }: PaginationProps) {
  const { current_page, total_pages, has_prev, has_next, total_count } = pagination

  if (total_pages <= 1) return null

  const startItem = (current_page - 1) * 10 + 1
  const endItem = Math.min(current_page * 10, total_count)

  const getPageNumbers = () => {
    const pages: (number | 'dots')[] = []
    const start = Math.max(1, current_page - 2)
    const end = Math.min(total_pages, current_page + 2)
    if (start > 1) pages.push(1)
    if (start > 2) pages.push('dots')
    for (let i = start; i <= end; i++) pages.push(i)
    if (end < total_pages - 1) pages.push('dots')
    if (end < total_pages) pages.push(total_pages)
    return pages
  }

  return (
    <div className="flex items-center justify-between gap-4">
      <p className="text-sm text-gray-500">
        Hiển thị <span className="font-medium text-gray-700">{startItem}</span> -{' '}
        <span className="font-medium text-gray-700">{endItem}</span> trong{' '}
        <span className="font-medium text-gray-700">{total_count}</span>
      </p>
      <nav className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(current_page - 1)}
          disabled={!has_prev}
          className={cn(
            'px-3 py-1.5 text-sm rounded-lg transition-colors cursor-pointer',
            has_prev ? 'text-gray-700 hover:bg-gray-100' : 'text-gray-300 cursor-not-allowed',
          )}
        >
          Trước
        </button>
        {getPageNumbers().map((p, i) =>
          p === 'dots' ? (
            <span key={`dots-${i}`} className="px-2 py-1.5 text-sm text-gray-400">...</span>
          ) : (
            <button
              key={p}
              onClick={() => onPageChange(p)}
              className={cn(
                'px-3 py-1.5 text-sm rounded-lg font-medium transition-colors cursor-pointer',
                p === current_page ? 'bg-brand-500 text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100',
              )}
            >
              {p}
            </button>
          ),
        )}
        <button
          onClick={() => onPageChange(current_page + 1)}
          disabled={!has_next}
          className={cn(
            'px-3 py-1.5 text-sm rounded-lg transition-colors cursor-pointer',
            has_next ? 'text-gray-700 hover:bg-gray-100' : 'text-gray-300 cursor-not-allowed',
          )}
        >
          Sau
        </button>
      </nav>
    </div>
  )
}
