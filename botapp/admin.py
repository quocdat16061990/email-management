from django.contrib import admin

from .models import Course, Customer, ChatGPTAccount


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name", "description")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "telegram_chat_id",
        "customer_email",
        "full_name",
        "phone_number",
        "is_staff",
        "course_list",
        "registration_date",
        "expiry_date",
        "status",
        "has_sent_otp",
        "created_at",
    )
    search_fields = ("telegram_chat_id", "customer_email", "full_name", "phone_number", "courses__name")
    list_filter = ("status", "has_sent_otp", "is_staff")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("courses")

    @admin.display(description="Courses")
    def course_list(self, obj: Customer) -> str:
        return ", ".join(course.name for course in obj.courses.all())


@admin.register(ChatGPTAccount)
class ChatGPTAccountAdmin(admin.ModelAdmin):
    list_display = ("email", "status", "imap_host", "created_at")
    search_fields = ("email",)
    list_filter = ("status", "imap_host")

