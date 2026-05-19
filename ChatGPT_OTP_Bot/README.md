# ChatGPT OTP Bot

Bot Telegram viết bằng Python + Django để lấy mã OTP đăng nhập ChatGPT từ Gmail chính và trả mã đó về lại Telegram.

## 1. Mục đích

Luồng hiện tại của bot là:

1. Người dùng nhắn `/start` trong Telegram.
2. Bot yêu cầu nhập email của người dùng.
3. Bot lưu email đó vào bảng `botapp_customer`.
4. Người dùng sang phía ChatGPT/OpenAI và bấm gửi mã OTP.
5. Người dùng quay lại Telegram và bấm nút `Lấy OTP từ Gmail OpenAI`.
6. Bot đăng nhập vào Gmail chính đã cấu hình trong file `.env`.
7. Bot quét email mới nhất từ OpenAI, lấy mã OTP 6 số.
8. Bot gửi OTP về Telegram.

Lưu ý quan trọng:

- Bot không quét email mà người dùng nhập.
- Bot chỉ quét Gmail chính được cấu hình bằng `EMAIL_ACCOUNT` và `APP_PASSWORD`.
- Email người dùng nhập hiện chỉ dùng để lưu thông tin khách hàng vào database.

## 2. Cấu trúc project

```text
ChatGPT_OTP_Bot/
├── botapp/
│   ├── bot.py
│   ├── keyboards.py
│   ├── models.py
│   ├── services.py
│   ├── migrations/
│   └── management/commands/run_otp_bot.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── .env
├── manage.py
├── migration.py
├── otp_bot.py
├── requirements.txt
└── README.md
```

Giải thích nhanh:

- `botapp/bot.py`: flow Telegram bot.
- `botapp/services.py`: logic kiểm tra email, quét Gmail, lấy OTP.
- `botapp/models.py`: model `Customer`.
- `botapp/keyboards.py`: các nút Telegram.
- `config/settings.py`: cấu hình Django.
- `manage.py run_otp_bot`: lệnh chạy bot.

## 3. Yêu cầu môi trường

Máy cần có:

- Python 3.11 hoặc 3.12
- pip
- PostgreSQL hoặc Supabase PostgreSQL
- Gmail có bật App Password
- Telegram bot token từ BotFather

## 4. Cài đặt thư viện

Chạy trong thư mục `ChatGPT_OTP_Bot`:

```powershell
pip install -r requirements.txt
```

## 5. Cấu hình file .env

Tạo hoặc cập nhật file `.env` với các biến sau:

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

Ý nghĩa từng biến:

- `TELEGRAM_BOT_TOKEN`: token bot Telegram lấy từ BotFather.
- `EMAIL_ACCOUNT`: Gmail chính dùng để nhận mail OTP từ OpenAI.
- `APP_PASSWORD`: App Password của Gmail đó.
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: cấu hình database PostgreSQL.

Lưu ý:

- Không dùng mật khẩu Gmail thường.
- Phải dùng App Password.
- Gmail này phải là email thực sự nhận được OTP từ OpenAI.

## 6. Tạo database table

Project hiện dùng Django migration và chỉ tạo bảng chính của bot.

Chạy:

```powershell
python manage.py migrate
```

Sau khi migrate, database tối thiểu sẽ có:

- `botapp_customer`
- `django_migrations`

## 7. Cấu trúc bảng customer

Bảng `botapp_customer` hiện có các cột:

- `telegram_chat_id`
- `customer_email`
- `status`
- `has_sent_otp`
- `created_at`

Ý nghĩa:

- `telegram_chat_id`: id chat Telegram của người dùng.
- `customer_email`: email người dùng nhập vào bot.
- `status`: trạng thái hiện tại, thường là `PENDING` hoặc `ACTIVE`.
- `has_sent_otp`: đánh dấu bot đã lấy được OTP từ mail OpenAI hay chưa.
- `created_at`: thời gian tạo record.

## 8. Chạy bot

Có 2 cách chạy.

Cách 1:

```powershell
python manage.py run_otp_bot
```

Cách 2:

```powershell
python otp_bot.py
```

Nếu bot chạy thành công, terminal sẽ hiện:

```text
Bot dang chay va lang nghe tin nhan...
```

## 9. Cách test từng bước

### Bước 1: Mở bot trong Telegram

- Tìm bot Telegram của bạn.
- Nhắn:

```text
/start
```

### Bước 2: Nhập email

Bot sẽ trả lời:

```text
Xin chào. Bấm /start để bắt đầu.

Vui lòng nhập email của bạn.
```

Bạn nhập email bất kỳ để lưu thông tin khách hàng.

### Bước 3: Yêu cầu OpenAI gửi OTP

Sau khi nhập email hợp lệ, bot sẽ báo:

```text
Email hợp lệ.
Bây giờ hãy bấm gửi OTP trên trang OpenAI, sau đó bấm nút bên dưới để tôi lấy OTP từ Gmail.
```

Lúc này:

- Sang trang ChatGPT/OpenAI.
- Bấm gửi mã OTP đăng nhập.

### Bước 4: Bấm nút lấy OTP

Quay lại Telegram và bấm:

```text
Lấy OTP từ Gmail OpenAI
```

### Bước 5: Bot quét Gmail

Bot sẽ:

- đăng nhập Gmail chính trong `.env`
- tìm email mới nhất từ OpenAI
- ưu tiên mail `From: OpenAI <noreply@tm1.openai.com>` hoặc mail OpenAI tương tự
- trích mã OTP 6 số trong nội dung mail

Thời gian chờ hiện tại:

- tối đa `1 phút`
- quét lại mỗi `5 giây`

### Bước 6: Nhận OTP trên Telegram

Nếu tìm thấy, bot trả:

```text
OTP OpenAI của bạn là: 123456
Xong rồi. Cảm ơn bạn.
```

## 10. Logic quét mail hiện tại

Bot đang quét:

- Gmail trong biến `EMAIL_ACCOUNT`
- không quét email mà người dùng nhập

Bot ưu tiên tìm:

- mail chưa đọc từ `openai`
- mail chưa đọc từ `tm.openai.com`
- mail chưa đọc có subject chứa `ChatGPT`
- mail chưa đọc có subject chứa `OpenAI`

Sau đó bot tiếp tục lọc:

- `From` phải thuộc OpenAI
- subject hoặc nội dung phải khớp mẫu OTP ChatGPT
- mail phải đủ mới so với thời điểm người dùng bấm lấy OTP

## 11. Log nằm ở đâu

Nếu bạn chạy bot nền, log thường nằm ở:

- `bot.out.log`
- `bot.err.log`

Những dòng log quan trọng:

- `Bat dau quet Gmail OTP...`
- `Ket qua search mail OpenAI...`
- `Dang xet mail...`
- `Tim thay OTP tu mail...`

Bạn có thể mở log để xem bot đang lấy mail nào, subject nào, date nào.

## 12. Các lỗi thường gặp

### Lỗi 1: Bot không chạy

Nguyên nhân thường gặp:

- thiếu `TELEGRAM_BOT_TOKEN`
- token sai
- thiếu package

Cách xử lý:

```powershell
pip install -r requirements.txt
python manage.py check
```

### Lỗi 2: Không đọc được Gmail

Nguyên nhân thường gặp:

- sai `EMAIL_ACCOUNT`
- sai `APP_PASSWORD`
- Gmail chưa bật App Password

Cách xử lý:

- kiểm tra lại `.env`
- tạo lại App Password của Gmail

### Lỗi 3: Bot lấy nhầm OTP cũ

Nguyên nhân:

- inbox có mail OpenAI cũ chưa đọc
- mail mới đến sớm hoặc muộn hơn thời điểm bấm nút

Cách xử lý:

- chỉ giữ mail OpenAI mới nhất
- xóa hoặc đánh dấu đã đọc các mail OTP OpenAI cũ
- bấm gửi OTP mới rồi mới bấm nút lấy OTP

### Lỗi 4: Bot quét lâu

Nguyên nhân:

- mail OpenAI đến chậm
- Gmail có nhiều mail chưa đọc

Cách xử lý:

- chờ đủ 1 phút
- dọn inbox chưa đọc
- gửi lại OTP từ OpenAI

## 13. Các lệnh hữu ích

Kiểm tra project:

```powershell
python manage.py check
```

Chạy migration:

```powershell
python manage.py migrate
```

Chạy bot:

```powershell
python manage.py run_otp_bot
```

Compile kiểm tra lỗi cú pháp:

```powershell
python -m py_compile botapp\bot.py botapp\services.py
```

## 14. Ghi chú bảo mật

- Không commit file `.env` lên GitHub.
- Không public `TELEGRAM_BOT_TOKEN`.
- Không public `APP_PASSWORD`.
- Nếu token Telegram đã lộ, nên vào BotFather để revoke và tạo token mới.

## 15. Tóm tắt ngắn

Nếu cần chạy nhanh:

```powershell
pip install -r requirements.txt
python manage.py migrate
python manage.py run_otp_bot
```

Sau đó:

1. vào Telegram
2. nhắn `/start`
3. nhập email
4. sang ChatGPT bấm gửi OTP
5. quay lại bấm `Lấy OTP từ Gmail OpenAI`
6. nhận OTP trong Telegram
