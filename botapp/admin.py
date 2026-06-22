from django.contrib import admin

from .models import Customer, ChatGPTAccount


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "telegram_chat_id",
        "customer_email",
        "full_name",
        "phone_number",
        "is_staff",
        "registration_date",
        "expiry_date",
        "status",
        "has_sent_otp",
        "created_at",
    )
    search_fields = ("telegram_chat_id", "customer_email", "full_name", "phone_number")
    list_filter = ("status", "has_sent_otp", "is_staff")


@admin.register(ChatGPTAccount)
class ChatGPTAccountAdmin(admin.ModelAdmin):
    list_display = ("email", "status", "imap_host", "created_at")
    search_fields = ("email",)
    list_filter = ("status", "imap_host")


