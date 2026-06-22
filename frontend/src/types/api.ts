export interface Pagination {
  current_page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
  next_page_number: number | null;
  prev_page_number: number | null;
  total_count: number;
}

export interface ApiSuccess<T = unknown> {
  success: true;
  message?: string;
  [key: string]: T | boolean | string | undefined;
}

export interface DashboardStats {
  total_students: number;
  active_count: number;
  pending_count: number;
  expired_count: number;
  total_courses: number;
}
