# 🔑 Hướng dẫn Cấu hình & Sử dụng Tính năng OTP ChatGPT Dùng Chung

Tài liệu này hướng dẫn cách cấu hình và chạy thử nghiệm tính năng quản lý tài khoản ChatGPT dùng chung và tự động quét/lấy mã OTP OpenAI qua Telegram Bot.

---

## 📋 Mục lục
1. [Cập nhật cơ sở dữ liệu (Migration)](#1-cập-nhật-cơ-sở-dữ-liệu-migration)
2. [Cấu hình Gmail (Bắt buộc để đọc OTP)](#2-cấu-hình-gmail-bắt-buộc-để-đọc-otp)
3. [Thêm tài khoản ChatGPT vào Database](#3-thêm-tài-khoản-chatgpt-vào-database)
4. [Phân quyền nhân viên (Staff)](#4-phân-quyền-nhân-viên-staff)
5. [Quy trình chạy thử nghiệm (Test) trên Telegram](#5-quy-trình-chạy-thử-nghiệm-test-trên-telegram)

---

## 1. Cập nhật cơ sở dữ liệu (Migration)

Sau khi pull code mới về, bạn cần cập nhật database (đã có thêm bảng `ChatGPTAccount` và cột `is_staff` trong bảng `Customer` từ file migration `0010_chatgptaccount_customer_is_staff.py`).

Chạy lệnh sau tại thư mục gốc của dự án:
```powershell
python manage.py migrate
```

---

## 2. Cấu hình Gmail (Bắt buộc để đọc OTP)

Để bot tự động đọc được mã OTP OpenAI được gửi về Gmail của tài khoản ChatGPT dùng chung, hòm thư đó cần được cấu hình như sau:

### Bước 2.1: Bật giao thức IMAP trong Gmail
1. Đăng nhập vào Gmail của tài khoản ChatGPT (Ví dụ: `chatgpt.plus01@gmail.com`).
2. Vào **Cài đặt (Settings)** (biểu tượng bánh răng) -> **Xem tất cả chế độ cài đặt (See all settings)**.
3. Chọn tab **Chuyển tiếp và POP/IMAP (Forwarding and POP/IMAP)**.
4. Ở mục **Truy cập qua IMAP (IMAP access)** -> Chọn **Bật IMAP (Enable IMAP)**.
5. Cuộn xuống và nhấn **Lưu thay đổi (Save Changes)**.

### Bước 2.2: Tạo mật khẩu ứng dụng (App Password)
Google không cho phép đăng nhập trực tiếp bằng mật khẩu chính của tài khoản Gmail nữa. Bạn phải dùng mật khẩu ứng dụng 16 ký tự:
1. Vào trang [Quản lý tài khoản Google](https://myaccount.google.com/) của email đó.
2. Đảm bảo tài khoản đã **bật Xác minh 2 bước (2-Step Verification)**.
3. Tìm kiếm từ khóa **"Mật khẩu ứng dụng"** (hoặc **"App passwords"**).
4. Chọn ứng dụng là **Thư (Mail)** và thiết bị tùy ý, sau đó nhấn **Tạo (Generate)**.
5. Copy mật khẩu gồm **16 ký tự** được cấp (ví dụ: `abcd efgh ijkl mnop`).

---

## 3. Thêm tài khoản ChatGPT vào Database

Bạn cần đăng ký thông tin tài khoản ChatGPT dùng chung kèm thông tin IMAP đã cấu hình ở bước trên vào database.

### Cách 1: Qua trang Django Admin (Khuyên dùng)
1. Truy cập [http://localhost:8000/admin/](http://localhost:8000/admin/)
2. Đăng nhập bằng tài khoản Superuser (nếu chưa có, tạo bằng lệnh `python manage.py createsuperuser`).
3. Vào mục **Chat gpt accounts** -> Chọn **Add Chat gpt account**.
4. Nhập các thông tin:
   * **Email ChatGPT:** Email của tài khoản ChatGPT.
   * **Mật khẩu đăng nhập:** Mật khẩu để login ChatGPT (dùng hiển thị cho Staff copy).
   * **IMAP Server:** `imap.gmail.com` (mặc định).
   * **IMAP Port:** `993` (mặc định).
   * **Mật khẩu ứng dụng Email (đọc OTP):** Mật khẩu 16 ký tự vừa tạo ở Bước 2.2.
   * **Trạng thái:** `ACTIVE`.

### Cách 2: Qua Python Shell (Thao tác nhanh)
Mở terminal và chạy lệnh:
```powershell
python manage.py shell -c "from botapp.models import ChatGPTAccount; ChatGPTAccount.objects.create(email='chatgpt.plus01@gmail.com', password='mat_khau_chatgpt', imap_host='imap.gmail.com', imap_port=993, imap_user='chatgpt.plus01@gmail.com', imap_password='mat_khau_ung_dung_16_ky_tu', status='ACTIVE')"
```

---

## 4. Phân quyền nhân viên (Staff)

Chỉ những tài khoản Telegram được liên kết với email có quyền **Staff** mới có thể sử dụng lệnh `/accounts` để lấy OTP của tài khoản dùng chung.

### Cách kiểm tra & Phân quyền:
* **Admin mặc định:** Email nào trùng khớp với `EMAIL_ADMIN` được định nghĩa trong file `.env` sẽ tự động có quyền Staff/Admin trên Bot.
* **Cấp quyền thủ công:**
  1. Vào Django Admin -> Mục **Customers**.
  2. Chọn học viên tương ứng.
  3. Tích chọn ô **Is staff** và nhấn **Save**.
  
  *(Hoặc chạy qua shell: `Customer.objects.filter(customer_email='email_can_cap_quyen@gmail.com').update(is_staff=True)`).*

---

## 5. Quy trình chạy thử nghiệm (Test) trên Telegram

Sau khi khởi chạy dự án (`start.bat` hoặc khởi chạy các terminal riêng biệt):

1. **Liên kết tài khoản:**
   * Tìm Bot Telegram của bạn, gõ lệnh `/start`.
   * Nhập email học viên đã được cấp quyền Staff ở trên và thực hiện liên kết.
2. **Xem danh sách tài khoản:**
   * Gõ lệnh `/accounts`.
   * Bot hiển thị danh sách các tài khoản ChatGPT Plus đang hoạt động kèm nút bấm lấy OTP.
3. **Test lấy mã OTP:**
   * Mở trình duyệt web đăng nhập ChatGPT bằng email/password hiển thị trên Bot.
   * Khi OpenAI yêu cầu nhập mã OTP, quay lại Telegram Bot và nhấn nút **Lấy OTP** của tài khoản đó.
   * Chờ khoảng 10-15 giây, bot sẽ tự động đọc Gmail và trả về mã OTP gồm 6 chữ số trực tiếp trên Telegram cho bạn!
