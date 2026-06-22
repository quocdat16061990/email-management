from functools import wraps
import json

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt

from .models import ChatGPTAccount, Customer
from .services import normalize_phone_number


SESSION_KEY = "webapp_authenticated"


def web_login_required(view_func):
    @wraps(view_func)
    def wrapped(request: HttpRequest, *args, **kwargs):
        if not request.session.get(SESSION_KEY):
            return redirect("login")
        return view_func(request, *args, **kwargs)

    return wrapped


def api_login_required(view_func):
    @wraps(view_func)
    def wrapped(request: HttpRequest, *args, **kwargs):
        if not request.session.get(SESSION_KEY):
            return JsonResponse({"error": "Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại."}, status=401)
        return view_func(request, *args, **kwargs)

    return wrapped


def _json_body(request: HttpRequest) -> tuple[dict, JsonResponse | None]:
    try:
        return json.loads(request.body or b"{}"), None
    except json.JSONDecodeError:
        return {}, JsonResponse({"error": "Dữ liệu JSON không hợp lệ."}, status=400)


def _account_payload(account: ChatGPTAccount) -> dict:
    return {
        "id": account.id,
        "email": account.email,
        "password": account.password,
        "imap_host": account.imap_host,
        "imap_port": account.imap_port,
        "imap_user": account.imap_user or "",
        "imap_password": account.imap_password,
        "status": account.status,
        "created_at": account.created_at.isoformat(),
        "updated_at": account.updated_at.isoformat(),
    }


def _customer_payload(customer: Customer) -> dict:
    allowed_ids = list(customer.allowed_chatgpt_accounts.values_list("id", flat=True))
    return {
        "id": customer.id,
        "full_name": customer.full_name,
        "customer_email": customer.customer_email,
        "phone_number": customer.phone_number,
        "status": customer.status,
        "registration_date": str(customer.registration_date) if customer.registration_date else None,
        "expiry_date": str(customer.expiry_date) if customer.expiry_date else None,
        "telegram_chat_id": customer.telegram_chat_id,
        "is_verified_telegram": customer.is_verified_telegram,
        "is_staff": customer.is_staff,
        "allowed_chatgpt_account_ids": allowed_ids,
        "chatgpt_access_mode": "custom" if allowed_ids else "default",
    }


def login_view(request: HttpRequest) -> HttpResponse:
    return redirect(f"{settings.FRONTEND_URL}/login")


@web_login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    return redirect(f"{settings.FRONTEND_URL}/dashboard")


@web_login_required
def chatgpt_accounts_view(request: HttpRequest) -> HttpResponse:
    return redirect(f"{settings.FRONTEND_URL}/chatgpt-accounts")


@web_login_required
def logout_view(request: HttpRequest) -> HttpResponse:
    request.session.flush()
    return redirect(f"{settings.FRONTEND_URL}/login")


@csrf_exempt
def api_login(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "Phương thức không được hỗ trợ."}, status=405)
    data, error = _json_body(request)
    if error:
        return error

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    if not email or not password:
        return JsonResponse({"error": "Email và mật khẩu không được để trống."}, status=400)
    if email == settings.WEBAPP_LOGIN_EMAIL.lower() and password == settings.WEBAPP_LOGIN_PASSWORD:
        request.session[SESSION_KEY] = True
        request.session["operator_email"] = email
        return JsonResponse({"success": True, "operator_email": email})
    return JsonResponse({"error": "Thông tin đăng nhập không chính xác."}, status=401)


@csrf_exempt
def api_logout(request: HttpRequest) -> JsonResponse:
    request.session.flush()
    return JsonResponse({"success": True})


@api_login_required
def api_dashboard_stats(request: HttpRequest) -> JsonResponse:
    return JsonResponse({
        "total_chatgpt_accounts": ChatGPTAccount.objects.count(),
        "active_chatgpt_accounts": ChatGPTAccount.objects.filter(status="ACTIVE").count(),
        "imap_error_accounts": ChatGPTAccount.objects.filter(status="ERROR").count(),
        "linked_customers": Customer.objects.filter(telegram_chat_id__isnull=False, is_verified_telegram=True).count(),
    })


@api_login_required
def api_dashboard_list(request: HttpRequest) -> JsonResponse:
    query = request.GET.get("q", "").strip()
    page_number = request.GET.get("page", 1)
    sort_by = request.GET.get("sort_by", "created_at").strip()
    sort_order = request.GET.get("sort_order", "desc").strip()
    status = request.GET.get("status", "").strip()

    allowed_sorts = {
        "full_name": Lower("full_name"),
        "customer_email": Lower("customer_email"),
        "phone_number": "phone_number",
        "created_at": "created_at",
        "expiry_date": "expiry_date",
        "status": "status",
    }
    sort_field = allowed_sorts.get(sort_by, "created_at")
    if isinstance(sort_field, str):
        order_by_args = [f"-{sort_field}" if sort_order == "desc" else sort_field, "-id"]
    else:
        order_by_args = [sort_field.desc() if sort_order == "desc" else sort_field.asc(), "-id"]

    qs = Customer.objects.prefetch_related("allowed_chatgpt_accounts").order_by(*order_by_args)
    if query:
        qs = qs.filter(Q(full_name__icontains=query) | Q(customer_email__icontains=query) | Q(phone_number__icontains=query))
    if status and status != "ALL":
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(page_number)
    customers = [_customer_payload(customer) for customer in page_obj]

    return JsonResponse({
        "students": customers,
        "customers": customers,
        "pagination": {
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
            "has_next": page_obj.has_next(),
            "has_prev": page_obj.has_previous(),
            "next_page_number": page_obj.next_page_number() if page_obj.has_next() else None,
            "prev_page_number": page_obj.previous_page_number() if page_obj.has_previous() else None,
            "total_count": paginator.count,
        },
        "operator_email": request.session.get("operator_email", ""),
    })


@csrf_exempt
@api_login_required
def api_dashboard_create(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "Phương thức không được hỗ trợ."}, status=405)
    data, error = _json_body(request)
    if error:
        return error
    email = data.get("customer_email", "").strip().lower()
    if not email:
        return JsonResponse({"error": "Email khách hàng không được để trống."}, status=400)
    customer = Customer.objects.create(
        customer_email=email,
        full_name=data.get("full_name", "").strip(),
        phone_number=normalize_phone_number(data.get("phone_number", "")),
        registration_date=data.get("registration_date") or None,
        expiry_date=data.get("expiry_date") or None,
        status=data.get("status", "ACTIVE"),
        is_staff=bool(data.get("is_staff", False)),
    )
    return JsonResponse({"success": True, "student": _customer_payload(customer)})


@csrf_exempt
@api_login_required
def api_dashboard_update(request: HttpRequest, id: int) -> JsonResponse:
    if request.method != "PUT":
        return JsonResponse({"error": "Phương thức không được hỗ trợ."}, status=405)
    data, error = _json_body(request)
    if error:
        return error
    customer = get_object_or_404(Customer, id=id)
    if data.get("customer_email"):
        customer.customer_email = data["customer_email"].strip().lower()
    customer.full_name = data.get("full_name", customer.full_name).strip()
    customer.phone_number = normalize_phone_number(data.get("phone_number", customer.phone_number))
    customer.registration_date = data.get("registration_date") or customer.registration_date
    customer.expiry_date = data.get("expiry_date") or customer.expiry_date
    customer.status = data.get("status", customer.status)
    customer.is_staff = bool(data.get("is_staff", customer.is_staff))
    customer.save()
    return JsonResponse({"success": True, "student": _customer_payload(customer)})


@csrf_exempt
@api_login_required
def api_dashboard_delete(request: HttpRequest, id: int) -> JsonResponse:
    customer = get_object_or_404(Customer, id=id)
    email = customer.customer_email
    customer.delete()
    return JsonResponse({"success": True, "message": f"Đã xóa khách hàng '{email}'."})


@csrf_exempt
@api_login_required
def api_customer_chatgpt_access_update(request: HttpRequest, id: int) -> JsonResponse:
    if request.method != "PUT":
        return JsonResponse({"error": "Phương thức không được hỗ trợ."}, status=405)
    data, error = _json_body(request)
    if error:
        return error

    customer = get_object_or_404(Customer, id=id)
    account_ids = data.get("account_ids", [])
    if not isinstance(account_ids, list):
        return JsonResponse({"error": "Danh sách tài khoản không hợp lệ."}, status=400)

    normalized_ids = sorted({int(account_id) for account_id in account_ids})
    accounts = ChatGPTAccount.objects.filter(id__in=normalized_ids)
    if accounts.count() != len(normalized_ids):
        return JsonResponse({"error": "Có tài khoản ChatGPT không tồn tại."}, status=400)

    customer.allowed_chatgpt_accounts.set(accounts)
    return JsonResponse({"success": True, "customer": _customer_payload(customer)})


@api_login_required
def api_chatgpt_accounts_list(request: HttpRequest) -> JsonResponse:
    query = request.GET.get("q", "").strip()
    page_number = request.GET.get("page", 1)
    all_accounts = request.GET.get("all", "false").lower() == "true"
    qs = ChatGPTAccount.objects.order_by("email")
    if query:
        qs = qs.filter(email__icontains=query)
    if all_accounts:
        accounts = [_account_payload(account) for account in qs]
        return JsonResponse({
            "accounts": accounts,
            "pagination": {
                "current_page": 1,
                "total_pages": 1,
                "has_next": False,
                "has_prev": False,
                "next_page_number": None,
                "prev_page_number": None,
                "total_count": len(accounts),
            },
        })

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(page_number)
    return JsonResponse({
        "accounts": [_account_payload(account) for account in page_obj],
        "pagination": {
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
            "has_next": page_obj.has_next(),
            "has_prev": page_obj.has_previous(),
            "next_page_number": page_obj.next_page_number() if page_obj.has_next() else None,
            "prev_page_number": page_obj.previous_page_number() if page_obj.has_previous() else None,
            "total_count": paginator.count,
        },
    })


@csrf_exempt
@api_login_required
def api_chatgpt_accounts_create(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "Phương thức không được hỗ trợ."}, status=405)
    data, error = _json_body(request)
    if error:
        return error
    account = ChatGPTAccount.objects.create(
        email=data.get("email", "").strip().lower(),
        password=data.get("password", ""),
        imap_host=data.get("imap_host", "imap.gmail.com").strip() or "imap.gmail.com",
        imap_port=int(data.get("imap_port") or 993),
        imap_user=data.get("imap_user", "").strip() or None,
        imap_password=data.get("imap_password", ""),
        status=data.get("status", "ACTIVE"),
    )
    return JsonResponse({"success": True, "account": _account_payload(account)})


@csrf_exempt
@api_login_required
def api_chatgpt_accounts_update(request: HttpRequest, id: int) -> JsonResponse:
    if request.method != "PUT":
        return JsonResponse({"error": "Phương thức không được hỗ trợ."}, status=405)
    data, error = _json_body(request)
    if error:
        return error
    account = get_object_or_404(ChatGPTAccount, id=id)
    for field in ["email", "password", "imap_host", "imap_password", "status"]:
        if field in data:
            setattr(account, field, data[field].strip().lower() if field == "email" else data[field])
    account.imap_port = int(data.get("imap_port") or account.imap_port)
    account.imap_user = data.get("imap_user", account.imap_user) or None
    account.save()
    return JsonResponse({"success": True, "account": _account_payload(account)})


@csrf_exempt
@api_login_required
def api_chatgpt_accounts_delete(request: HttpRequest, id: int) -> JsonResponse:
    account = get_object_or_404(ChatGPTAccount, id=id)
    email = account.email
    account.delete()
    return JsonResponse({"success": True, "message": f"Đã xóa tài khoản ChatGPT '{email}'."})
