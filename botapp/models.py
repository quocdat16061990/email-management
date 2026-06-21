from django.db import models
from django.utils.text import slugify


class Course(models.Model):
    spotlight_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    web_link = models.URLField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class CourseLink(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="links")
    title = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.title} ({self.course.name})"


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
    telegram_otp = models.CharField(max_length=6, null=True, blank=True)
    telegram_otp_created_at = models.DateTimeField(null=True, blank=True)
    courses = models.ManyToManyField(Course, through="Enrollment", blank=True, related_name="customers")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        identifier = self.telegram_chat_id if self.telegram_chat_id is not None else "chua-link-telegram"
        return f"{self.customer_email} ({identifier})"

    def sync_overall_fields(self) -> None:
        enrolls = list(self.enrollments.all())
        if not enrolls:
            return
        
        reg_dates = [e.registration_date for e in enrolls if e.registration_date]
        self.registration_date = min(reg_dates) if reg_dates else None
        
        exp_dates = [e.expiry_date for e in enrolls if e.expiry_date]
        self.expiry_date = max(exp_dates) if exp_dates else None
        
        statuses = [e.status for e in enrolls]
        if "ACTIVE" in statuses:
            self.status = "ACTIVE"
        elif "PENDING" in statuses:
            self.status = "PENDING"
        else:
            self.status = "EXPIRED"
            
        self.save(update_fields=["registration_date", "expiry_date", "status"])



class Enrollment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    registration_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default="ACTIVE")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.customer.customer_email} - {self.course.name} ({self.status})"


class ChatGPTAccount(models.Model):
    email = models.EmailField(unique=True, verbose_name="Email ChatGPT")
    password = models.CharField(max_length=255, verbose_name="Mật khẩu đăng nhập")
    
    # Cấu hình IMAP để bot tự động đọc OTP
    imap_host = models.CharField(max_length=255, default="imap.gmail.com", verbose_name="IMAP Server")
    imap_port = models.IntegerField(default=993, verbose_name="IMAP Port")
    imap_user = models.CharField(max_length=255, blank=True, null=True, verbose_name="IMAP Username")
    imap_password = models.CharField(max_length=255, verbose_name="Mật khẩu ứng dụng Email (đọc OTP)")
    
    status = models.CharField(
        max_length=20, 
        choices=[("ACTIVE", "Đang hoạt động"), ("INACTIVE", "Khóa/Tạm dừng"), ("ERROR", "Lỗi cấu hình mail")], 
        default="ACTIVE",
        verbose_name="Trạng thái"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.email} ({self.status})"

