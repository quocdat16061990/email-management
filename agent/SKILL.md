---
name: email-management
description: Thiết lập toàn bộ hệ thống Anhlaptrinh Management trên máy mới. Dùng khi người dùng yêu cầu "cài đặt", "setup", "migrate database", "chạy hệ thống", "cài đặt môi trường". Bao gồm: kiểm tra môi trường Python/Node, tạo .env, cài thư viện backend + frontend, migrate Supabase, chạy 3 thành phần (Django + React + Telegram Bot).
---

# skill_setup_email_management

> Kỹ năng thiết lập toàn bộ hệ thống **Anhlaptrinh Management** trên máy mới.
> Dành cho Claude Code / Codex Agent khi được yêu cầu "cài đặt", "setup", "migrate", "chạy hệ thống".

---

## 📂 Thành phần

| File | Chức năng |
|---|---|
| `setup.bat` | Script cài đặt tự động cho Windows |
| `setup.sh` | Script cài đặt tự động cho Linux/Mac |
| `.env.example` | Mẫu file biến môi trường |
| `requirements.txt` | Thư viện Python |
| `frontend/package.json` | Thư viện Node |

---

## 🚀 Yêu cầu trước khi cài đặt

### Người dùng phải tự chuẩn bị

| Thông tin | Hướng dẫn lấy |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Tạo bot tại [@BotFather](https://t.me/BotFather) → gửi `/newbot` → nhận token |
| `EMAIL_ACCOUNT` + `APP_PASSWORD` | Gmail → Quản lý Tài khoản → Bảo mật → Mật khẩu ứng dụng |
| `DB_HOST`...`DB_PASSWORD` | [Supabase](https://supabase.com) → New Project → Project Settings → Database → Connection string |

---

## ⚙️ Hướng dẫn sử dụng cho Agent (AI / Codex)

### A. Cài đặt lần đầu (First-time Setup)

Khi người dùng yêu cầu "cài đặt", "setup", "chạy thử", agent phải thực hiện các bước sau theo đúng thứ tự:

#### Bước 1: Kiểm tra môi trường

```bash
python --version  # yêu cầu >= 3.10
node --version    # yêu cầu >= 18
npm --version     # yêu cầu >= 9
```

#### Bước 2: Kiểm tra file `.env`

File `.env` phải tồn tại và đã được điền đầy đủ thông tin.

Nếu chưa có, tạo từ `.env.example`:
```bash
cp .env.example .env
```

**Các trường bắt buộc phải kiểm tra:**
- `TELEGRAM_BOT_TOKEN` — không được để trống hoặc giá trị mẫu
- `EMAIL_ACCOUNT` + `APP_PASSWORD` — không được để trống
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` — đủ 5 trường

Nếu thiếu, yêu cầu người dùng cung cấp trước khi tiếp tục.

#### Bước 3: Cài thư viện Backend

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

#### Bước 4: Cài thư viện Frontend

```bash
cd frontend
npm install
cd ..
```

#### Bước 5: Migrate Database

> ⚠️ **Bắt buộc dùng Supabase PostgreSQL.** Đảm bảo 5 trường DB trong `.env` đã điền đúng.

```bash
python manage.py migrate
```

Kiểm tra thành công:
```bash
python manage.py showmigrations
# Tất cả phải có dấu [X]
```

#### Bước 6: Khởi động ứng dụng (3 terminal riêng)

```bash
# Terminal 1 — Backend
python manage.py runserver

# Terminal 2 — Frontend
cd frontend && npm run dev

# Terminal 3 — Telegram Bot
python manage.py run_otp_bot
```

---

### B. Cấu trúc thư mục

```
Email-Management/
├── botapp/                    # Backend Python
│   ├── bot.py                 # Telegram bot
│   ├── services.py            # Business logic (OTP, lookup)
│   ├── models.py              # Course, Customer, Enrollment
│   ├── views.py               # API endpoints
│   └── urls.py                # URL routing
├── config/                    # Django settings
├── frontend/                  # React TypeScript SPA
├── manage.py                  # Django CLI
├── requirements.txt           # Python dependencies
├── .env                       # Biến môi trường (tự tạo)
├── .env.example               # Mẫu biến môi trường
├── setup.bat                  # Script cài Windows
├── setup.sh                   # Script cài Linux/Mac
├── SKILL.md                   # File này
└── SUMMARY_FOR_BOSS.md        # Báo cáo cho sếp
```

---

### C. Các lỗi thường gặp

| Vấn đề | Nguyên nhân | Fix |
|---|---|---|
| `.env` thiếu thông tin | Chưa điền hoặc còn giá trị mẫu | Kiểm tra và điền đầy đủ |
| `migrate` lỗi kết nối | Sai DB_HOST, DB_USER, DB_PASSWORD | Kiểm tra thông tin Supabase |
| Bot "Conflict" | Bot instance khác đang chạy | `taskkill /f /im python.exe` hoặc `killall python` |
| CORS error | FRONTEND_URL sai port | Sửa lại đúng port Vite |
| `npm install` lỗi | Mất network hoặc xung đột | Xóa `node_modules`, chạy lại |
| Vite port bận | Port 5173 đã dùng | `npm run dev -- --port 5174` |

---

### D. Các lệnh hữu ích

```bash
# Kiểm tra migrations
python manage.py showmigrations

# Kiểm tra kết nối database
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.db import connection
connection.ensure_connection()
print('DB OK')
"
```

---

### E. Bug đã fix

| Bug | Mô tả | Fix |
|---|---|---|
| #001 | `endTime` sai múi giờ → thiếu học viên Voomly | Dùng `timezone.localtime()` thay `timezone.now()` |
| #002 | Bot crash vì ORM trong async không wrap | Wrap mọi ORM query với `sync_to_async` |

---

### F. Chuẩn Codex / Claude Code

- Xác định HĐH trước khi chạy lệnh
- Đường dẫn linh hoạt, không hardcode
- Kiểm tra `.env` trước mọi thao tác
