from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("telegram_chat_id", "customer_email", "status", "has_sent_otp", "created_at")
    search_fields = ("telegram_chat_id", "customer_email")
    list_filter = ("status", "has_sent_otp")
