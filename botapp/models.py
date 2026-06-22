from django.db import models


class Customer(models.Model):
    telegram_chat_id = models.BigIntegerField(unique=True, null=True, blank=True)
    customer_email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, default="")
    full_name = models.CharField(max_length=255, blank=True, default="")
    registration_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default="ACTIVE")
    has_sent_otp = models.BooleanField(default=False)
    is_verified_telegram = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    allowed_chatgpt_accounts = models.ManyToManyField(
        "ChatGPTAccount",
        blank=True,
        related_name="allowed_customers",
        verbose_name="Tài khoản ChatGPT được cấp riêng",
    )
    telegram_otp = models.CharField(max_length=6, null=True, blank=True)
    telegram_otp_created_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        identifier = self.telegram_chat_id if self.telegram_chat_id is not None else "chưa-link-telegram"
        return f"{self.customer_email} ({identifier})"


class ChatGPTAccount(models.Model):
    email = models.EmailField(unique=True, verbose_name="Email ChatGPT")
    password = models.CharField(max_length=255, verbose_name="Mật khẩu đăng nhập")

    # Cấu hình IMAP để bot tự động đọc OTP.
    imap_host = models.CharField(max_length=255, default="imap.gmail.com", verbose_name="IMAP Server")
    imap_port = models.IntegerField(default=993, verbose_name="IMAP Port")
    imap_user = models.CharField(max_length=255, blank=True, null=True, verbose_name="IMAP Username")
    imap_password = models.CharField(max_length=255, verbose_name="Mật khẩu ứng dụng Email (đọc OTP)")

    status = models.CharField(
        max_length=20,
        choices=[
            ("ACTIVE", "Đang hoạt động"),
            ("INACTIVE", "Khóa/Tạm dừng"),
            ("ERROR", "Lỗi cấu hình mail"),
        ],
        default="ACTIVE",
        verbose_name="Trạng thái",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.email} ({self.status})"
