export interface Course {
  id: number;
  name: string;
  description: string;
  web_link: string;
  links: CourseLink[];
  created_at?: string;
  student_count?: number;
}

export interface CourseLink {
  title: string;
  url: string;
}
