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
  status: string;
  registration_date: string | null;
  expiry_date: string | null;
  enrollments: {
    course_id: number;
    course_name: string;
    registration_date: string | null;
    expiry_date: string | null;
    status: string;
  }[];
}

export interface StudentSearchResult {
  id: number;
  full_name: string;
  customer_email: string;
  phone_number: string;
  is_enrolled: boolean;
}
