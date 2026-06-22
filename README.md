# 🎓 Anhlaptrinh Management — Hệ thống Quản lý Học viên & Bot Telegram OTP

> **Mô tả dự án:** Hệ thống quản lý học viên tập trung, tự động hóa việc lấy mã OTP OpenAI qua Telegram, Giao diện web dashboard hiện đại (React SPA) giúp admin quản lý học viên, khóa học, đăng ký — tất cả trên một nền tảng duy nhất.

---

### 🎯 Vấn đề được giải quyết

1. **OTP OpenAI thủ công** — Trước đây học viên phải tự tay lấy mã OTP từ Gmail → mất thời gian, sai sót. Bot Telegram tự động quét Gmail, trả OTP trong 5-30 giây.
2. **Quản lý học viên rời rạc** — Không có dashboard tập trung. Nay admin xem được toàn bộ học viên, khóa học, trạng thái đăng ký trên một giao diện web.
4. **Tra cứu chậm** — Học viên gọi điện hỏi thông tin → admin lookup Telegram, có ngay email, tên, SĐT, khóa học, trạng thái.

### 📊 Lợi ích kinh doanh

| Chỉ tiêu | Trước | Sau |
|---|---|---|
| Thời gian lấy OTP | 2-5 phút (thủ công) | 5-30 giây (tự động) |
| Tra cứu học viên | Mở DB / hỏi lại | /lookup Telegram, 1 giây |
| Giao diện quản lý | Không có | Dashboard React SPA |
| Load lại trang khi thao tác | Có (Django templates) | Không (React SPA mượt mà) |

### 🏗 Kiến trúc tổng thể

```
Người dùng cuối (Học viên)               Admin (Nhân viên)
        │                                       │
        ▼                                       ▼
┌─────────────────┐                  ┌──────────────────────┐
│  Telegram Bot   │                  │  React Web Dashboard │
│  (lấy OTP, xem  │                  │  (Quản lý học viên,  │
│   khóa học)     │                  │   khóa học, đồng bộ) │
└────────┬────────┘                  └──────────┬───────────┘
         │                                       │
         └───────────────┬───────────────────────┘
                         ▼
               ┌──────────────────┐
               │  Django Backend  │ ←── Supabase PostgreSQL
               │  (REST API)      │
               └──────────────────┘

---

## 📦 Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| **Backend** | Django (Python) — REST API thuần (không DRF) |
| **Frontend** | React 19 + TypeScript + Vite + Tailwind CSS |
| **Data Fetching** | TanStack React Query |
| **Form** | React Hook Form + Zod |
| **UI Library** | shadcn/ui |
| **Bot** | python-telegram-bot (PTB v21) |
| **Database** | PostgreSQL (Supabase) / SQLite (local) |
| **Email** | Gmail IMAP (lấy OTP OpenAI) |
| **Auth** | Session cookie (Django session) |

---

## 🏗 Kiến trúc tổng thể

```
Trình duyệt (React SPA @ localhost:5173)
         │
         ├── /api/*  ──proxy──>  Django API @ :8000
         │
         └── Telegram Bot ──>    Django @ :8000
Database: Supabase PostgreSQL / SQLite
```

### Flow dữ liệu chính

1. **Web Dashboard**: React gọi API Django → Django query DB → trả JSON
2. **Telegram Bot**: User nhập email → Bot lưu chat_id → User gửi OTP → Bot quét Gmail → trả OTP

---

## 📁 Cấu trúc thư mục

```
.
├── botapp/                        # Ứng dụng Django chính
│   ├── bot.py                     # Telegram bot handlers
│   ├── keyboards.py               # Inline keyboard Telegram
│   ├── services.py                # Business logic (OTP, lookup)
│   ├── models.py                  # Course, Customer, Enrollment, CourseLink
│   ├── views.py                   # API endpoints (HTML + JSON)
│   ├── urls.py                    # URL routing
│   ├── middleware.py              # CORS middleware
│   ├── forms.py                   # Django forms (legacy)
│   ├── admin.py                   # Admin config
│   └── migrations/                # DB migrations
├── config/                        # Cấu hình Django
│   ├── settings.py                # Settings chính
│   └── urls.py                    # Root URL config
├── frontend/                      # React SPA
│   ├── src/
│   │   ├── api/                   # API client functions
│   │   ├── hooks/                 # React Query hooks
│   │   ├── context/               # AuthContext
│   │   ├── components/            # React components
│   │   │   ├── layout/            # Header, AppLayout
│   │   │   ├── shared/            # SearchInput, Pagination, StatusBadge...
│   │   │   ├── students/          # StudentFormModal...
│   │   │   └── courses/           # CourseFormModal, EnrollStudentModal...
│   │   ├── pages/                 # Login, Dashboard, Courses, CourseDetail, StudentDetail
│   │   ├── types/                 # TypeScript interfaces
│   │   ├── lib/                   # Utility functions
│   │   ├── App.tsx                # Router + QueryClient
│   │   ├── main.tsx               # Entry point
│   │   └── index.css              # Tailwind + custom theme
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
├── .env.example                   # Mẫu file biến môi trường
├── .gitignore                     # File bỏ qua khi push git
├── manage.py                      # Django CLI
├── requirements.txt               # Python dependencies
└── README.md                      # File này
```

---

## 🚀 Cài đặt

### Yêu cầu

- **Python** >= 3.10
- **Node.js** >= 18
- **Git**

### 1. Clone dự án

```powershell
git clone <đường-dẫn-repo>
cd Email-Management
```

### 2. Backend — Cài Python

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend — Cài Node

```powershell
cd frontend
npm install
cd ..
```

### 4. Tạo file biến môi trường

```powershell
copy .env.example .env
```

Mở file `.env` và điền thông tin:

```env
# ─── Telegram Bot ────────────────────────────
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
EMAIL_ACCOUNT=your_gmail_address
APP_PASSWORD=your_gmail_app_password

# ─── Web Dashboard Login ─────────────────────
COMPANY_NAME=Anhlaptrinh Management
COMPANY_LOGO_TEXT=AL
WEBAPP_LOGIN_EMAIL=admin@example.com
WEBAPP_LOGIN_PASSWORD=change-me

# ─── Database (Supabase PostgreSQL) ──────────
# Nếu điền đủ 5 trường → dùng PostgreSQL
# Nếu để trống → tự động dùng SQLite local
DB_HOST=aws-1-ap-northeast-2.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.xxxxx
DB_PASSWORD=your_password


# ─── React Frontend URL (CORS) ──────────────
FRONTEND_URL=http://localhost:5173
```

> **Lưu ý về Database:**
> - Nếu điền đủ `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` → Django dùng **PostgreSQL Supabase**
> - Nếu thiếu bất kỳ trường nào → Django tự động dùng **SQLite** (file `db.sqlite3`)

### 5. Migrate database

```powershell
python manage.py migrate
```

Câu lệnh này sẽ tạo tất cả các bảng:
- `botapp_course` — Khóa học
- `botapp_courselink` — Liên kết học tập
- `botapp_customer` — Học viên
- `botapp_enrollment` — Đăng ký khóa học (bảng trung gian)

---

## 🏃 Chạy ứng dụng

Cần **3 terminal** riêng biệt:

### Terminal 1 — Django Backend

```powershell
cd d:\Email-Management
python manage.py runserver
# → http://127.0.0.1:8000/
```

### Terminal 2 — React Frontend

```powershell
cd d:\Email-Management\frontend
npm run dev
# → http://localhost:5173/
```

### Terminal 3 — Telegram Bot

```powershell
cd d:\Email-Management
python manage.py run_otp_bot
# Bot đang chạy và lắng nghe tin nhắn...
```

### Hoặc chạy bot bằng:

```powershell
python otp_bot.py
```

---

## 🌐 Hướng dẫn sử dụng Web Dashboard

Mở `http://localhost:5173/` (hoặc `http://127.0.0.1:8000/` sẽ redirect sang React).

### Đăng nhập

| Trường | Giá trị mặc định |
|---|---|
| Email | `admin@example.com` (hoặc giá trị trong `.env`) |
| Mật khẩu | `change-me` (hoặc giá trị trong `.env`) |

### Các trang

| Route | Chức năng |
|---|---|
| `/dashboard` | Quản lý học viên (thêm, sửa, xóa, tìm kiếm) |
| `/students/:id` | Chi tiết học viên + danh sách khóa học đã đăng ký |
| `/courses` | Quản lý khóa học (thêm, sửa, xóa) |
| `/courses/:id` | Chi tiết khóa học + danh sách học viên |

### Tính năng chính

- **Thêm học viên**: Form modal với chọn khóa học + ngày đăng ký/hết hạn
- **Tìm kiếm**: Debounce 300ms, tìm theo tên/email/SĐT
- **Phân trang**: 10 items/trang
- **Thêm học viên vào khóa học**: Tìm kiếm học viên có sẵn hoặc tạo mới

---

## 🤖 Telegram Bot

### Tìm bot trên Telegram

Tìm theo tên bot của bạn (dựa vào `TELEGRAM_BOT_TOKEN`).

### Các lệnh

| Lệnh | Chức năng |
|---|---|
| `/start` | Bắt đầu / Liên kết tài khoản Telegram với email |
| `/me` | Xem thông tin cá nhân (email, tên, SĐT, khóa học) |
| `/courses` | Xem danh sách khóa học đã đăng ký (có phân trang) |
| `/otp` | Lấy mã OTP OpenAI nhanh (nếu đã liên kết email) |
| `/lookup <email \| SĐT>` | Tra cứu thông tin học viên (Admin) |
| `/help` | Hướng dẫn sử dụng |

### Luồng hoạt động OTP

```
1. User gõ /start
2. Bot gửi tin nhắn chào mừng + yêu cầu nhập email
3. User nhập email → Bot kiểm tra + liên kết Telegram chat_id với Customer
4. User truy cập OpenAI → gửi mã OTP
5. User bấm nút "🔑 Lấy OTP" → Bot quét Gmail (IMAP)
6. Bot trả về mã OTP 6 số
```

### Menu Inline Keyboard

Sau khi liên kết thành công, bot hiển thị menu:
```
👤 Thông tin của tôi
📚 Khóa học của tôi
🔑 Lấy mã OTP
❓ Trợ giúp
```

- **Thông tin của tôi**: Xem email, tên, SĐT, trạng thái, số khóa học
- **Khóa học của tôi**: Danh sách khóa học (phân trang 5/trang), click vào xem chi tiết (ngày hết hạn, còn bao nhiêu ngày)
- **Lấy mã OTP**: Quét Gmail tìm OTP OpenAI
- **Trợ giúp**: Hướng dẫn các lệnh

---


## 📡 API Endpoints — Đầy đủ

### Auth

| Method | URL | Chức năng |
|---|---|---|
| POST | `/api/login/` | Đăng nhập (trả về session cookie) |
| POST | `/api/logout/` | Đăng xuất (xóa session) |

### Dashboard / Students

| Method | URL | Chức năng |
|---|---|---|
| GET | `/api/dashboard/` | Danh sách học viên (query: `q`, `page`) |
| GET | `/api/dashboard/stats/` | Thống kê tổng quan |
| POST | `/api/dashboard/create/` | Tạo học viên + enrollments |
| PUT | `/api/dashboard/:id/` | Cập nhật học viên |
| DELETE | `/api/dashboard/:id/delete/` | Xóa học viên |
| GET | `/api/students/:id/` | Chi tiết học viên + enrollments |
| GET | `/courses/search-students/` | Tìm kiếm học viên (query: `q`, `course_id`, `page`) |

### Courses

| Method | URL | Chức năng |
|---|---|---|
| GET | `/api/courses/` | Danh sách khóa học (query: `page`) |
| POST | `/api/courses/create/` | Tạo khóa học + links |
| PUT | `/api/courses/:id/update/` | Cập nhật khóa học |
| DELETE | `/api/courses/:id/delete/` | Xóa khóa học |
| GET | `/api/courses/:id/` | Chi tiết khóa học + danh sách học viên |
| POST | `/courses/update-website/` | Cập nhật link website khóa học |

### Enrollments

| Method | URL | Chức năng |
|---|---|---|
| POST | `/api/enroll/` | Đăng ký học viên vào khóa học |

---

## 🗄 Database Schema

### Course

| Field | Type | Ghi chú |
|---|---|---|
| `id` | AutoField | PK |
| `name` | CharField(255) | unique |
| `description` | TextField | |
| `web_link` | URLField(500) | Auto-generate từ name nếu trống |
| `created_at` | DateTimeField | auto_now_add |

### Customer

| Field | Type | Ghi chú |
|---|---|---|
| `id` | AutoField | PK |
| `telegram_chat_id` | BigIntegerField | unique, nullable |
| `customer_email` | EmailField | unique |
| `phone_number` | CharField(20) | |
| `full_name` | CharField(255) | |
| `registration_date` | DateField | nullable — min của enrollments |
| `expiry_date` | DateField | nullable — max của enrollments |
| `status` | CharField(20) | ACTIVE / PENDING / EXPIRED |
| `has_sent_otp` | BooleanField | |
| `created_at` | DateTimeField | auto_now_add |

### Enrollment (bảng trung gian)

| Field | Type | Ghi chú |
|---|---|---|
| `id` | AutoField | PK |
| `customer` | FK → Customer | CASCADE |
| `course` | FK → Course | CASCADE |
| `registration_date` | DateField | nullable |
| `expiry_date` | DateField | nullable |
| `status` | CharField(20) | ACTIVE / PENDING / EXPIRED |
| `created_at` | DateTimeField | auto_now_add |

### CourseLink

| Field | Type | Ghi chú |
|---|---|---|
| `id` | AutoField | PK |
| `course` | FK → Course | CASCADE, related_name="links" |
| `title` | CharField(255) | |
| `url` | URLField(500) | |
| `created_at` | DateTimeField | auto_now_add |

---

## 🐙 Git — File nào push, file nào bỏ qua?

### 🔒 Bị bỏ qua (`.gitignore`)

| File / Thư mục | Lý do |
|---|---|
| `.env` | **Chứa mật khẩu, token — bí mật tuyệt đối!** |
| `venv/`, `.venv/` | Môi trường ảo Python |
| `frontend/node_modules/` | Thư viện Node |
| `frontend/dist/` | Build output |
| `__pycache__/`, `*.pyc` | Cache bytecode Python |
| `db.sqlite3` | Database local |
| `*.log` | File log runtime |
| `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` | Cache dev tools |
| `.coverage`, `htmlcov/` | Báo cáo test |
| `.DS_Store`, `Thumbs.db` | File hệ thống |

### ✅ Được push lên git

| File | Mục đích |
|---|---|
| `botapp/` | Code Python (models, views, services, bot) |
| `config/` | Cấu hình Django |
| `frontend/src/` | Code React TypeScript |
| `frontend/package.json` | Dependencies Node |
| `frontend/vite.config.ts` | Vite config |
| `frontend/index.html` | HTML entry |
| `manage.py` | Django CLI |
| `requirements.txt` | Python dependencies |
| `.env.example` | Mẫu cho người khác copy thành `.env` |
| `.gitignore` | Danh sách ignore |

---

## 💻 Cài đặt trên máy khác

```powershell
# 1. Clone
git clone <url-repo>
cd Email-Management

# 2. Backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 3. Frontend
cd frontend
npm install
cd ..

# 4. Tạo .env
copy .env.example .env
# ⚠️ Mở .env và điền: token Telegram, Gmail, database...

# 5. Migrate DB
python manage.py migrate

# 6. Chạy thử (3 terminal)
python manage.py runserver           # Django :8000
cd frontend && npm run dev           # React :5173
python manage.py run_otp_bot         # Telegram bot
```

> **Quan trọng**: File `.env` không được đồng bộ qua git. Mỗi máy tự tạo.
> Nếu cần chia sẻ `.env`, gửi qua kênh riêng (email, cloud mật).

---

## 🔧 Troubleshooting

### Bot Telegram lỗi "Conflict: terminated by other getUpdates request"

```powershell
taskkill /f /im python.exe
# Sau đó chạy lại bot
python manage.py run_otp_bot
```

### CORS lỗi khi React gọi API

Kiểm tra `.env` có `FRONTEND_URL=http://localhost:5173` và Django settings có CORS middleware.

### Database migration lỗi

```powershell
python manage.py migrate --run-syncdb
python manage.py showmigrations
```

---

## 📚 Liên kết

- [Kế hoạch chuyển đổi React](.claude/plans/agile-exploring-sparrow.md) — Lộ trình React migration

---

*Hệ thống được phát triển bởi **Anh Lập Trình** — Trợ lý **Thu Nhi** hỗ trợ quản lý học tập.*
