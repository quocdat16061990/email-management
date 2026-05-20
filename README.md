# ChatGPT OTP Bot

Bot Telegram viết bằng Python + Django để lấy mã OTP đăng nhập ChatGPT/OpenAI từ Gmail chính và trả mã đó về lại Telegram.

## Cấu trúc project

```text
.
|-- botapp/
|-- config/
|-- .env.example
|-- keyboards.py
|-- manage.py
|-- migration.py
|-- otp_bot.py
|-- requirements.txt
`-- README.md
```

## Cài đặt

```powershell
pip install -r requirements.txt
```

Tạo file `.env` từ `.env.example`, rồi cấu hình tối thiểu:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
EMAIL_ACCOUNT=your_gmail_address
APP_PASSWORD=your_gmail_app_password
DB_HOST=your_db_host
DB_PORT=your_db_port
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

## Chạy project

```powershell
python manage.py migrate
python manage.py run_otp_bot
```

Hoặc:

```powershell
python otp_bot.py
```

## Ghi chú

- Project hiện đã được đưa thẳng ra repo root, không còn nằm trong thư mục `ChatGPT_OTP_Bot/`.
- Không commit `.env`, log hoặc cache Python lên Git.
