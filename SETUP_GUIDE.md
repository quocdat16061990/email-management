# 📦 Hướng dẫn Cài đặt Hệ thống Anhlaptrinh Management

> Tài liệu dành cho Developer / IT Support — chạy 1 lệnh là xong.
> **BẮT BUỘC dùng Supabase PostgreSQL** — không hỗ trợ SQLite.

---

## 📋 Yêu cầu

| Công cụ | Kiểm tra |
|---|---|
| Python >= 3.10 | `python --version` |
| Node.js >= 18 | `node --version` |
| Git | `git --version` |

---

## 🚀 Cài đặt (1 lệnh)

### Bước 1: Điền thông tin vào `.env`

```powershell
copy .env.example .env
```

Mở file `.env` và điền đầy đủ các thông tin sau:

| Biến | Hướng dẫn lấy |
|---|---|
| `TELEGRAM_BOT_TOKEN` | [@BotFather](https://t.me/BotFather) trên Telegram |
| `EMAIL_ACCOUNT` + `APP_PASSWORD` | Gmail → App Password |
| `DB_HOST`...`DB_PASSWORD` | Supabase → Project Settings → Database |
| `VOOMLY_BEARER_TOKEN` | Voomly Dashboard → Settings → API |

### Bước 3: Chạy file setup

> ⚠️ **Đảm bảo đã điền đầy đủ .env trước khi chạy**

```powershell
setup.bat
```

File này sẽ tự động:
1. Cài thư viện Python (pip install)
2. Cài thư viện Frontend (npm install)
3. Migrate database Supabase
4. Đồng bộ dữ liệu từ Voomly (khóa học + học viên)

### Bước 4: Chạy ứng dụng (3 terminal)

```powershell
# Terminal 1 — Backend
python manage.py runserver

# Terminal 2 — Frontend
cd frontend && npm run dev

# Terminal 3 — Telegram Bot
python manage.py run_otp_bot
```

Mở trình duyệt: `http://localhost:5173/` — Email: `admin@example.com` / Mật khẩu: `change-me`

---

## ❌ Lỗi thường gặp

| Lỗi | Fix |
|---|---|
| `.env` thiếu thông tin | `setup.bat` sẽ báo lỗi cụ thể — điền đủ rồi chạy lại |
| Database migrate lỗi | Kiểm tra lại `DB_HOST`, `DB_USER`, `DB_PASSWORD` trong `.env` |
| Bot "Conflict" | `taskkill /f /im python.exe` rồi chạy lại bot |
| CORS | Kiểm tra `FRONTEND_URL` trong `.env` đúng port Vite |
