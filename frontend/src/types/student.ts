export interface Student {
  id: number;
  full_name: string;
  customer_email: string;
  phone_number: string;
  status: 'ACTIVE' | 'PENDING' | 'EXPIRED';
  registration_date: string | null;
  expiry_date: string | null;
  telegram_chat_id?: number | null;
  is_verified_telegram?: boolean;
  is_staff?: boolean;
  allowed_chatgpt_account_ids?: number[];
  chatgpt_access_mode?: 'default' | 'custom';
  created_at?: string;
  enrollments?: EnrollmentDetail[];
}

export interface EnrollmentDetail {
  course_id: number;
  course_name: string;
  course_description?: string;
  web_link?: string;
  links?: { title: string; url: string }[];
  registration_date: string | null;
  expiry_date: string | null;
  status: string;
}

export interface StudentListItem {
  id: number;
  full_name: string;
  customer_email: string;
  phone_number: string;
  status: 'ACTIVE' | 'PENDING' | 'EXPIRED';
  registration_date: string | null;
  expiry_date: string | null;
  telegram_chat_id?: number | null;
  is_verified_telegram?: boolean;
  is_staff?: boolean;
  allowed_chatgpt_account_ids?: number[];
  chatgpt_access_mode?: 'default' | 'custom';
  enrollments?: EnrollmentDetail[];
}

export interface StudentSearchResult {
  id: number;
  full_name: string;
  customer_email: string;
  phone_number: string;
  is_enrolled: boolean;
}
