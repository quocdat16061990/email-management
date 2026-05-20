from django.db import models


class Customer(models.Model):
    telegram_chat_id = models.BigIntegerField(unique=True)
    customer_email = models.EmailField(unique=True)
    status = models.CharField(max_length=20, default="ACTIVE")
    has_sent_otp = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.customer_email} ({self.telegram_chat_id})"
