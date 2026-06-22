from datetime import timedelta

from django import forms
from django.utils import timezone

from .models import Course
from .services import is_valid_email


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email đăng nhập")
    password = forms.CharField(label="Mật khẩu", widget=forms.PasswordInput)


class CustomerRegistrationForm(forms.Form):
    full_name = forms.CharField(label="Họ tên học viên", max_length=255)
    customer_email = forms.EmailField(label="Email học viên")
    phone_number = forms.CharField(label="Số điện thoại", max_length=20)
    existing_courses = forms.ModelMultipleChoiceField(
        label="Khóa học đã có",
        queryset=Course.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    extra_courses = forms.CharField(
        label="Thêm khóa học mới",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Mỗi dòng là một khóa học mới.",
    )
    registration_date = forms.DateField(
        label="Ngày đăng ký",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )
    expiry_date = forms.DateField(
        label="Ngày hết hạn",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )
    status = forms.ChoiceField(
        label="Trạng thái",
        choices=[("ACTIVE", "Đang hoạt động"), ("PENDING", "Chờ xử lý"), ("EXPIRED", "Đã hết hạn")],
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["existing_courses"].queryset = Course.objects.order_by("name")
        today = timezone.localdate()
        self.fields["registration_date"].initial = today
        self.fields["expiry_date"].initial = today + timedelta(days=30)
        self.fields["status"].initial = "ACTIVE"

    def clean_customer_email(self) -> str:
        customer_email = self.cleaned_data["customer_email"].strip().lower()
        if not is_valid_email(customer_email):
            raise forms.ValidationError("Email học viên không hợp lệ.")
        return customer_email

    def clean_phone_number(self) -> str:
        raw_phone = self.cleaned_data["phone_number"].strip()
        digits = "".join(char for char in raw_phone if char.isdigit())
        if len(digits) < 8:
            raise forms.ValidationError("Số điện thoại phải có ít nhất 8 chữ số.")
        return digits

    def clean(self):
        cleaned_data = super().clean()
        registration_date = cleaned_data.get("registration_date")
        expiry_date = cleaned_data.get("expiry_date")
        if registration_date and expiry_date and expiry_date < registration_date:
            self.add_error("expiry_date", "Ngày hết hạn phải lớn hơn hoặc bằng ngày đăng ký.")
        return cleaned_data

    def get_course_names(self) -> list[str]:
        existing_courses = [course.name for course in self.cleaned_data.get("existing_courses", [])]
        extra_courses = [
            line.strip()
            for line in self.cleaned_data.get("extra_courses", "").splitlines()
            if line.strip()
        ]
        return existing_courses + extra_courses
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["name", "description", "web_link"]
        labels = {
            "name": "Tên khóa học",
            "description": "Mô tả khóa học",
            "web_link": "Link website khóa học",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ví dụ: Python Basic"}),
            "description": forms.Textarea(attrs={"placeholder": "Nhập mô tả khóa học...", "rows": 3}),
            "web_link": forms.TextInput(attrs={"placeholder": "Ví dụ: https://example.com/course (để trống sẽ tự động tạo link mặc định)"}),
        }

    def clean_name(self) -> str:
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("Tên khóa học không được để trống.")
        # Check uniqueness case-insensitively
        qs = Course.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Tên khóa học này đã tồn tại.")
        return name

