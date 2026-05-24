# HƯỚNG DẪN CẬP NHẬT: XÁC THỰC EMAIL OTP KHI LIÊN KẾT TELEGRAM

Tài liệu này hướng dẫn cách cài đặt, chạy migration, cấu hình và kiểm thử tính năng xác thực OTP qua Email trước khi liên kết tài khoản Telegram của học viên.

---

## 1. Các Thay Đổi Mã Nguồn

### 1.1 Cơ sở dữ liệu (Database Models)
Thêm 3 trường mới vào class `Customer` trong file `botapp/models.py`:
- `is_verified_telegram = models.BooleanField(default=False)`
- `telegram_otp = models.CharField(max_length=6, null=True, blank=True)`
- `telegram_otp_created_at = models.DateTimeField(null=True, blank=True)`

### 1.2 Cấu hình Django (`config/settings.py`)
- Thêm `BASE_DIR / "emails"` vào danh sách `TEMPLATES["DIRS"]` để Django tìm thấy template email.
- Thêm cấu hình SMTP Gmail ở cuối file:
  ```python
  EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
  EMAIL_HOST = "smtp.gmail.com"
  EMAIL_PORT = 587
  EMAIL_USE_TLS = True
  EMAIL_HOST_USER = EMAIL_ACCOUNT
  EMAIL_HOST_PASSWORD = APP_PASSWORD
  DEFAULT_FROM_EMAIL = f"{COMPANY_NAME} <{EMAIL_ACCOUNT}>"
  ```

### 1.3 Logic Nghiệp vụ & Gửi Email (`botapp/services.py`)
- Thêm hàm `get_or_create_customer_for_otp(email, otp_code)`: Tạo/tìm học viên theo email và lưu mã OTP cùng thời gian tạo. Lúc này chưa cập nhật `telegram_chat_id` của họ để bảo mật.
- Thêm hàm `send_telegram_otp_email(to_email, otp_code)`: Sử dụng `EmailMultiAlternatives` gửi email dạng HTML (`otp_email.html`) lẫn Text (`otp_email.txt`) tới học viên.

### 1.4 Luồng Hội thoại Telegram Bot (`botapp/bot.py`)
- Định nghĩa trạng thái hội thoại mới: `ASK_OTP = 1`.
- Cập nhật `_find_customer_by_chat_id` để chỉ tìm các học viên đã có `is_verified_telegram=True`.
- Cập nhật hàm `handle_email`: Tạo mã OTP ngẫu nhiên 6 chữ số, lưu vào DB và gửi qua Email, sau đó chuyển sang trạng thái `ASK_OTP`.
- Thêm hàm `handle_otp`: Nhận OTP từ người dùng, kiểm tra khớp mã và thời hạn 10 phút. Nếu nhập sai quá 5 lần sẽ huỷ phiên. Nếu đúng sẽ tiến hành liên kết Telegram Chat ID và đánh dấu `is_verified_telegram=True`.
- Cập nhật `build_application` để đăng ký trạng thái `ASK_OTP` và cho phép nút "Bắt đầu lại" (`restart_flow`) hoạt động ở cả 2 bước.

### 1.5 Giao diện Quản trị (Admin UI)
- **Backend API (`botapp/views.py`)**: Hàm `api_student_detail` trả về thêm trường `is_verified_telegram`.
- **Frontend Types (`frontend/src/types/student.ts`)**: Thêm `is_verified_telegram?: boolean;` vào interface `Student`.
- **Chi tiết Học viên (`frontend/src/pages/StudentDetailPage.tsx`)**: Hiển thị nhãn **Đã xác thực** (màu xanh lá) hoặc **Chưa xác thực** (màu cam) bên cạnh Telegram Chat ID.

---

## 2. Hướng Dẫn Cài Đặt & Chạy Dự Án

### Bước 1: Cập nhật biến môi trường (`.env`)
Đảm bảo file `.env` đã khai báo đúng thông tin Gmail của bạn:
```env
EMAIL_ACCOUNT=ten_email_cua_ban@gmail.com
APP_PASSWORD=ma_ung_dung_gmail_16_ky_tu
COMPANY_NAME=Tên Học Viện Của Bạn
```

### Bước 2: Chạy Database Migration
Mở Terminal ở thư mục gốc của dự án và chạy các lệnh:
```bash
# Tạo file migration mới cho Customer model
python manage.py makemigrations

# Thực thi cập nhật cơ sở dữ liệu (Supabase / Postgres / SQLite)
python manage.py migrate
```

### Bước 3: Biên dịch lại Frontend
```bash
cd frontend
npm run build
```

### Bước 4: Chạy dự án
Chạy Backend Server:
```bash
python manage.py runserver
```
Mở một cửa sổ terminal khác và chạy Telegram Bot:
```bash
python otp_bot.py
```

## 3. Các Phương Pháp Hỗ Trợ Kiểm Thử (Testing & Debugging)

### 3.1 Lệnh `/unlink` trực tiếp trên Telegram (Khuyên dùng)
Bạn có thể gõ lệnh **`/unlink`** trực tiếp trong ô chat Telegram ở bất kỳ thời điểm nào. Lệnh này sẽ:
- Tìm học viên đang liên kết với tài khoản Telegram đó và đặt `telegram_chat_id = None`, `is_verified_telegram = False`.
- Đưa bot quay trở lại màn hình yêu cầu nhập email ngay lập tức để bạn bắt đầu luồng test mới.

---

### 3.2 Lệnh Terminal để xoá liên kết Telegram của email bất kỳ
Nếu bạn muốn đặt lại một email cụ thể từ dòng lệnh Backend để test lại:

Chạy lệnh sau trong Terminal ở thư mục gốc dự án:
```bash
python manage.py shell -c "from botapp.models import Customer; Customer.objects.filter(customer_email='ten_email_can_xoa@gmail.com').update(telegram_chat_id=None, is_verified_telegram=False)"
```
*(Thay thế `ten_email_can_xoa@gmail.com` bằng email của bạn cần kiểm thử).*

---

### 3.3 Lệnh Terminal để kiểm tra trạng thái liên kết hiện tại
```bash
python manage.py shell -c "from botapp.models import Customer; c = Customer.objects.filter(customer_email='ten_email_can_kiem_tra@gmail.com').first(); print('Họ tên:', c.full_name if c else 'Không tìm thấy', '| Chat ID:', c.telegram_chat_id if c else 'Chưa liên kết', '| Xác thực:', c.is_verified_telegram if c else 'Chưa xác thực')"
```
