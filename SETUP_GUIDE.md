# 📦 Hướng dẫn Cài đặt Hệ thống Anhlaptrinh Management

> Tài liệu dành cho Developer / IT Support — hướng dẫn cài đặt toàn bộ hệ thống từ clone code đến chạy được.
> **BẮT BUỘC dùng Supabase PostgreSQL** — không hỗ trợ SQLite trong môi trường production.

---

## 📋 Yêu cầu

| Công cụ | Phiên bản tối thiểu | Kiểm tra |
|---|---|---|
| Python | >= 3.10 | `python --version` |
| Node.js | >= 18 | `node --version` |
| npm | >= 9 | `npm --version` |
| Git | bất kỳ | `git --version` |

---

## 🚀 Quy trình cài đặt (8 bước)

### Bước 1: Clone dự án

```powershell
git clone <đường-dẫn-repo>
cd Email-Management
```

### Bước 2: Cài đặt Backend (Python)

```powershell
# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường ảo
venv\Scripts\activate

# Cài thư viện Python
pip install -r requirements.txt
```

### Bước 3: Cài đặt Frontend (Node)

```powershell
# Di chuyển vào thư mục frontend
cd frontend

# Cài thư viện Node
npm install

# Quay về thư mục gốc
cd ..
```

### Bước 4: Tạo file biến môi trường

```powershell
copy .env.example .env
```

**Mở file `.env` bằng Notepad hoặc VS Code và điền thông tin của bạn.**

Danh sách các thông tin **bắt buộc phải nhập**:

#### 🔑 Telegram Bot Token
> Lấy tại: [@BotFather](https://t.me/BotFather) trên Telegram

```env
TELEGRAM_BOT_TOKEN=nhập_token_của_bạn_vào_đây
```

#### 📧 Gmail & App Password (cho tính năng OTP)
> Hướng dẫn tạo App Password: https://myaccount.google.com/apppasswords

```env
EMAIL_ACCOUNT=email_của_bạn@gmail.com
APP_PASSWORD=mật_khẩu_app_của_bạn
```

#### 🌐 Web Dashboard Login
```env
COMPANY_NAME=Anhlaptrinh Management
COMPANY_LOGO_TEXT=AL
WEBAPP_LOGIN_EMAIL=admin@example.com
WEBAPP_LOGIN_PASSWORD=change-me
```

> ⚠️ **Nên đổi mật khẩu** sau khi cài đặt lần đầu.

#### 🗄️ Supabase Database (BẮT BUỘC)
> Đăng ký tại: https://supabase.com — tạo project mới, lấy thông tin kết nối ở **Project Settings → Database**

```env
DB_HOST=aws-1-ap-northeast-2.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.tên_project_của_bạn
DB_PASSWORD=mật_khẩu_DB_của_bạn
```

> ⚠️ **Bắt buộc**: Hệ thống chỉ hoạt động với Supabase PostgreSQL. Phải điền đủ 5 trường trên.

#### 🔄 Voomly API Token (cho đồng bộ khóa học & học viên)
> Lấy tại: Voomly Dashboard → Settings → API

```env
VOOMLY_BEARER_TOKEN=nhập_token_Voomly_của_bạn
```

> Nếu chưa có token, bạn vẫn có thể chạy hệ thống nhưng sẽ không đồng bộ được dữ liệu từ Voomly.

#### 🌍 React Frontend URL
```env
FRONTEND_URL=http://localhost:5173
```

> Nếu chạy React ở port khác, sửa lại cho đúng.

### Bước 5: Migrate Database

```powershell
python manage.py migrate
```

Lệnh này sẽ tạo tất cả bảng trong Supabase:

| Bảng | Mục đích |
|---|---|
| `botapp_course` | Khóa học |
| `botapp_courselink` | Liên kết học tập |
| `botapp_customer` | Học viên |
| `botapp_enrollment` | Đăng ký khóa học |
| `botapp_enrollment` + các bảng Django system | Session, ContentType... |

Kiểm tra thành công:

```powershell
python manage.py showmigrations
```

Tất cả phải có dấu `[X]` ở trước.

> 💡 **Dữ liệu đã có sẵn trên Supabase?** Nếu Supabase đã có dữ liệu từ trước, migrate chỉ tạo bảng nếu chưa có — dữ liệu cũ vẫn còn nguyên.

### Bước 6: Đồng bộ dữ liệu từ Voomly (quan trọng)

Sau khi migrate thành công, database đang **rỗng** (chưa có khóa học, chưa có học viên).  
Bạn cần đồng bộ từ Voomly để có dữ liệu.

#### Cách 3: Qua Python script

Tạo file `scripts/sync_data.py`:

```python
import os, django, time
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from botapp.services import sync_courses_from_voomly, sync_all_students_from_voomly
from botapp.models import Course, Customer

print("📚 Đồng bộ khóa học từ Voomly...")
start = time.time()
res = sync_courses_from_voomly()
print(f"✅ Xong: {res} — {time.time()-start:.2f}s")
print(f"   Tổng khóa học hiện tại: {Course.objects.count()}")

print()
print("👥 Đồng bộ học viên từ Voomly...")
start = time.time()
res = sync_all_students_from_voomly()
print(f"✅ Xong: {res} — {time.time()-start:.2f}s")
print(f"   Tổng học viên hiện tại: {Customer.objects.count()}")
```

Chạy:

```powershell
python scripts/sync_data.py
```

### Bước 7: Chạy thử (3 terminal)

**Terminal 1 — Django Backend:**
```powershell
cd d:\Email-Management
venv\Scripts\activate
python manage.py runserver
# → http://127.0.0.1:8000/
```

**Terminal 2 — React Frontend:**
```powershell
cd d:\Email-Management\frontend
npm run dev
# → http://localhost:5173/
```

**Terminal 3 — Telegram Bot:**
```powershell
cd d:\Email-Management
venv\Scripts\activate
python manage.py run_otp_bot
# → Bot đang chạy...
```

### Bước 8: Đăng nhập Web

Mở trình duyệt: `http://localhost:5173/`

| Tài khoản | Giá trị mặc định |
|---|---|
| Email | `admin@example.com` |
| Mật khẩu | `change-me` |

> Đổi mật khẩu trong `.env` nếu cần.

---

## ❌ Các lỗi thường gặp

### Lỗi kết nối Supabase

```powershell
# Kiểm tra .env có đúng 5 trường DB không
# Kiểm tra kết nối thủ công:
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection
connection.ensure_connection()
print('Kết nối DB OK!')
"
```

### Lỗi migrate

```powershell
# Nếu migrate lỗi, kiểm tra bảng đã tồn tại chưa:
python manage.py showmigrations

# Nếu bảng đã có mà migrate báo lỗi, giả mạo:
python manage.py migrate --fake
```

### Lỗi Bot Telegram "Conflict"

```powershell
taskkill /f /im python.exe
python manage.py run_otp_bot
```

### Lỗi Vite port trùng

```powershell
netstat -ano | findstr :5173
taskkill /PID <số> /F
```

### Lỗi CORS

Kiểm tra `FRONTEND_URL` trong `.env` phải đúng với port Vite đang chạy.

---

## 📂 Cấu trúc thư mục dự án

```text
Email-Management/
├── botapp/                    # Backend Python
│   ├── bot.py                 # Telegram bot
│   ├── services.py            # Logic đồng bộ Voomly, OTP, lookup
│   ├── models.py              # Course, Customer, Enrollment
│   ├── views.py               # API endpoints
│   └── urls.py                # URL routing
├── config/
│   ├── settings.py            # Django settings
│   └── urls.py                # Root URL config
├── frontend/                  # Frontend React
│   ├── src/
│   │   ├── pages/             # Login, Dashboard, Courses...
│   │   ├── components/        # Component UI
│   │   ├── api/               # API client
│   │   └── hooks/             # React Query hooks
│   ├── package.json
│   └── vite.config.ts
├── manage.py
├── requirements.txt
├── .env                       # Biến môi trường (tự tạo, không push git)
├── SETUP_GUIDE.md             # File hướng dẫn này
├── VOOMLY_SYNC_GUIDE.md       # Tài liệu kỹ thuật đồng bộ Voomly
└── SUMMARY_FOR_BOSS.md        # Báo cáo cho sếp
```

---

## 🔧 File chạy tự động (tuỳ chọn)

Tạo file `setup.bat` ở thư mục gốc:

```batch
@echo off
chcp 65001 >nul
echo ===== CAI DAT HE THONG ANHLAPTRINH MANAGEMENT =====
echo.

echo [1/5] Tao moi truong ao Python...
python -m venv venv
call venv\Scripts\activate

echo [2/5] Cai thu vien Python...
pip install -r requirements.txt
echo OK.

echo [3/5] Cai thu vien Node...
cd frontend
npm install
cd ..
echo OK.

echo [4/5] Tao file .env tu .env.example...
if not exist .env (
    copy .env.example .env
    echo.
    echo === DA TAO FILE .env ===
    echo >>> HAY MO .env VA DIEN DAY DU THONG TIN <<<
    echo >>> - TELEGRAM_BOT_TOKEN         (tu @BotFather)
    echo >>> - EMAIL_ACCOUNT + APP_PASSWORD (tu Gmail)
    echo >>> - DB_HOST ... DB_PASSWORD    (tu Supabase)
    echo >>> - VOOMLY_BEARER_TOKEN        (tu Voomly)
    echo.
) else (
    echo .env da ton tai, bo qua.
)

echo [5/5] Migrate database...
python manage.py migrate
echo OK.

echo.
echo ===== XONG! =====
echo.
echo Tiep theo:
echo   1. Mo .env va dien thong tin neu chua lam
echo   2. Chay 3 terminal:
echo      Terminal 1: python manage.py runserver
echo      Terminal 2: cd frontend ^&^& npm run dev
echo      Terminal 3: python manage.py run_otp_bot
echo   3. Dong bo Voomly: vao Web hoac dung script
echo.
pause
```

> Lưu thành `setup.bat`, nhấp đôi để chạy.
> Sau khi chạy, **nhớ mở `.env` và điền thông tin** trước khi start server.

---

## 🔄 Tham khảo: Quy trình đồng bộ Voomly

> Chi tiết: [VOOMLY_SYNC_GUIDE.md](VOOMLY_SYNC_GUIDE.md)

### API Voomly

| API | URL | Mục đích |
|---|---|---|
| Lấy khóa học | `GET https://api.voomly.com/spotlights?tiny=1` | Đồng bộ danh sách khóa học |
| Lấy học viên | `GET https://api.voomly.com/spotlights/{id}/customers` | Đồng bộ học viên theo khóa |
| Thêm học viên | `POST https://api.voomly.com/spotlights/{id}/customers` | Thêm học viên lên Voomly |

### Bug đã fix

| Bug | Mô tả | Fix |
|---|---|---|
| #001 | `endTime` sai múi giờ → thiếu học viên | Dùng `timezone.localtime()` thay `timezone.now()` |
| #002 | Bot crash vì ORM trong async context | Wrap query với `sync_to_async` |
