from django import forms

from .services import is_valid_email


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email đăng nhập")
    password = forms.CharField(label="Mật khẩu", widget=forms.PasswordInput)


class CustomerRegistrationForm(forms.Form):
    full_name = forms.CharField(label="Họ tên khách hàng", max_length=255, required=False)
    customer_email = forms.EmailField(label="Email khách hàng")
    phone_number = forms.CharField(label="Số điện thoại", max_length=20, required=False)

    def clean_customer_email(self) -> str:
        customer_email = self.cleaned_data["customer_email"].strip().lower()
        if not is_valid_email(customer_email):
            raise forms.ValidationError("Email khách hàng không hợp lệ.")
        return customer_email

    def clean_phone_number(self) -> str:
        raw_phone = self.cleaned_data.get("phone_number", "").strip()
        return "".join(char for char in raw_phone if char.isdigit())
