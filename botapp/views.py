from functools import wraps

import json
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .forms import CourseForm, CustomerRegistrationForm, LoginForm
from .models import Course, CourseLink, Customer, Enrollment
from .services import (
    add_student_to_voomly,
    fetch_students_for_course,
    normalize_phone_number,
    sync_all_students_from_voomly,
    sync_courses_from_voomly,
    wait_for_voomly_student,
    upsert_customer_from_web,
)


SESSION_KEY = "webapp_authenticated"


def _base_context() -> dict[str, str]:
    return {
        "company_name": settings.COMPANY_NAME,
        "company_logo_text": settings.COMPANY_LOGO_TEXT,
    }


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


def login_view(request: HttpRequest) -> HttpResponse:
    return redirect(f"{settings.FRONTEND_URL}/login")


@web_login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    return redirect(f"{settings.FRONTEND_URL}/dashboard")


@web_login_required
def logout_view(request: HttpRequest) -> HttpResponse:
    request.session.flush()
    return redirect(f"{settings.FRONTEND_URL}/login")


@web_login_required
def courses_view(request: HttpRequest) -> HttpResponse:
    return redirect(f"{settings.FRONTEND_URL}/courses")


@api_login_required
def student_detail_api(request: HttpRequest) -> JsonResponse:
    student_id = request.GET.get("id")
    if not student_id:
        return JsonResponse({"error": "Missing student ID"}, status=400)

    student = get_object_or_404(Customer, id=student_id)
    courses_ids = list(student.courses.values_list("id", flat=True))
    
    enrollments_data = []
    for enroll in student.enrollments.all():
        enrollments_data.append({
            "course_id": enroll.course_id,
            "registration_date": str(enroll.registration_date) if enroll.registration_date else "",
            "expiry_date": str(enroll.expiry_date) if enroll.expiry_date else "",
            "status": enroll.status,
        })

    return JsonResponse({
        "id": student.id,
        "full_name": student.full_name,
        "customer_email": student.customer_email,
        "phone_number": student.phone_number,
        "status": student.status,
        "registration_date": str(student.registration_date) if student.registration_date else "",
        "expiry_date": str(student.expiry_date) if student.expiry_date else "",
        "courses": courses_ids,
        "enrollments": enrollments_data,
    })


@api_login_required
def course_detail_api(request: HttpRequest) -> JsonResponse:
    course_id = request.GET.get("id")
    if not course_id:
        return JsonResponse({"error": "Missing course ID"}, status=400)

    course = get_object_or_404(Course, id=course_id)
    links_data = [{"title": link.title, "url": link.url} for link in course.links.all()]
    return JsonResponse({
        "id": course.id,
        "name": course.name,
        "spotlight_id": course.spotlight_id or "",
        "description": course.description or "",
        "web_link": course.web_link or "",
        "links": links_data,
    })



@web_login_required
def student_detail_view(request: HttpRequest, student_id: int) -> HttpResponse:
    return redirect(f"{settings.FRONTEND_URL}/students/{student_id}")


@api_login_required
def sync_courses_view(request: HttpRequest) -> HttpResponse:
    try:
        result = sync_courses_from_voomly()
        return JsonResponse({"success": True, "result": result})
    except Exception as e:
        return JsonResponse({"error": f"Lỗi đồng bộ: {e}"}, status=500)


@csrf_exempt
@api_login_required
def update_course_website_api(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "Phương thức không được hỗ trợ"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Dữ liệu JSON không hợp lệ"}, status=400)

    course_id = data.get("id")
    web_link = data.get("web_link", "").strip()

    if not course_id:
        return JsonResponse({"error": "Thiếu ID khóa học"}, status=400)

    course = get_object_or_404(Course, id=course_id)
    course.web_link = web_link
    course.save(update_fields=["web_link"])

    return JsonResponse({
        "success": True,
        "message": f"Đã cập nhật website cho khóa học '{course.name}' thành công.",
        "web_link": course.web_link
    })


@api_login_required
def sync_students_view(request: HttpRequest) -> HttpResponse:
    try:
        result = sync_all_students_from_voomly()
        return JsonResponse({"success": True, "result": result})
    except Exception as e:
        return JsonResponse({"error": f"Lỗi đồng bộ: {e}"}, status=500)


@api_login_required
def student_search_api(request: HttpRequest) -> JsonResponse:
    query = request.GET.get("q", "").strip()
    page_number = request.GET.get("page", 1)
    course_id = request.GET.get("course_id")

    students_query = Customer.objects.all().order_by("-created_at")
    if query:
        from django.db.models import Q
        students_query = students_query.filter(
            Q(full_name__icontains=query) |
            Q(customer_email__icontains=query) |
            Q(phone_number__icontains=query)
        )

    enrolled_student_ids = set()
    if course_id:
        from .models import Enrollment
        enrolled_student_ids = set(
            Enrollment.objects.filter(course_id=course_id).values_list("customer_id", flat=True)
        )

    from django.core.paginator import Paginator
    paginator = Paginator(students_query, 10)
    
    try:
        page_obj = paginator.page(page_number)
    except Exception:
        page_obj = paginator.page(1)

    students_data = []
    for s in page_obj:
        students_data.append({
            "id": s.id,
            "full_name": s.full_name,
            "customer_email": s.customer_email,
            "phone_number": s.phone_number,
            "is_enrolled": s.id in enrolled_student_ids
        })

    return JsonResponse({
        "students": students_data,
        "pagination": {
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
            "has_next": page_obj.has_next(),
            "has_prev": page_obj.has_previous(),
            "next_page_number": page_obj.next_page_number() if page_obj.has_next() else None,
            "prev_page_number": page_obj.previous_page_number() if page_obj.has_previous() else None,
            "total_count": paginator.count
        }
    })


@web_login_required
def enroll_student_view(request: HttpRequest) -> HttpResponse:
    return redirect(f"{settings.FRONTEND_URL}/courses")


@web_login_required
def course_detail_view(request: HttpRequest, course_id: int) -> HttpResponse:
    return redirect(f"{settings.FRONTEND_URL}/courses/{course_id}")


# ─── API: Auth ────────────────────────────────────────────────────────────────

@csrf_exempt
def api_login(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

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


# ─── API: Dashboard / Students ───────────────────────────────────────────────

@api_login_required
def api_dashboard_list(request: HttpRequest) -> JsonResponse:
    query = request.GET.get("q", "").strip()
    page_number = request.GET.get("page", 1)

    qs = Customer.objects.prefetch_related("enrollments__course").order_by("-created_at")
    if query:
        qs = qs.filter(Q(full_name__icontains=query) | Q(customer_email__icontains=query) | Q(phone_number__icontains=query))

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(page_number)

    students_data = []
    for s in page_obj:
        enrollments = [
            {
                "course_id": e.course_id,
                "course_name": e.course.name,
                "registration_date": str(e.registration_date) if e.registration_date else None,
                "expiry_date": str(e.expiry_date) if e.expiry_date else None,
                "status": e.status,
            }
            for e in s.enrollments.all()
        ]
        students_data.append({
            "id": s.id,
            "full_name": s.full_name,
            "customer_email": s.customer_email,
            "phone_number": s.phone_number,
            "status": s.status,
            "registration_date": str(s.registration_date) if s.registration_date else None,
            "expiry_date": str(s.expiry_date) if s.expiry_date else None,
            "enrollments": enrollments,
        })

    return JsonResponse({
        "students": students_data,
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
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    email = data.get("customer_email", "").strip().lower()
    if not email:
        return JsonResponse({"error": "Email học viên không được để trống."}, status=400)

    full_name = data.get("full_name", "").strip()
    phone = normalize_phone_number(data.get("phone_number", ""))

    customer, created = Customer.objects.get_or_create(
        customer_email=email,
        defaults={"full_name": full_name, "phone_number": phone},
    )
    if not created:
        if full_name:
            customer.full_name = full_name
        if phone:
            customer.phone_number = phone
        customer.save()

    # Process enrollments
    enrollments_data = data.get("enrollments", [])
    customer.enrollments.all().delete()
    for enc in enrollments_data:
        course_id = enc.get("course_id")
        if not course_id:
            continue
        reg_date = _parse_date(enc.get("registration_date")) or timezone.localdate()
        exp_date = _parse_date(enc.get("expiry_date")) or (reg_date + timedelta(days=365))
        status = enc.get("status", "ACTIVE")
        Enrollment.objects.create(customer=customer, course_id=course_id, registration_date=reg_date, expiry_date=exp_date, status=status)

    customer.sync_overall_fields()
    return JsonResponse({
        "success": True,
        "student": {
            "id": customer.id,
            "full_name": customer.full_name,
            "customer_email": customer.customer_email,
            "phone_number": customer.phone_number,
            "status": customer.status,
        },
    })


@csrf_exempt
@api_login_required
def api_dashboard_update(request: HttpRequest, id: int) -> JsonResponse:
    if request.method != "PUT":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    customer = get_object_or_404(Customer, id=id)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    email = data.get("customer_email", "").strip().lower()
    full_name = data.get("full_name", "").strip()
    phone = normalize_phone_number(data.get("phone_number", ""))

    if email and email != customer.customer_email:
        customer.customer_email = email
    if full_name:
        customer.full_name = full_name
    if phone:
        customer.phone_number = phone
    customer.save()

    enrollments_data = data.get("enrollments", [])
    customer.enrollments.all().delete()
    for enc in enrollments_data:
        course_id = enc.get("course_id")
        if not course_id:
            continue
        reg_date = _parse_date(enc.get("registration_date")) or timezone.localdate()
        exp_date = _parse_date(enc.get("expiry_date")) or (reg_date + timedelta(days=365))
        status = enc.get("status", "ACTIVE")
        Enrollment.objects.create(customer=customer, course_id=course_id, registration_date=reg_date, expiry_date=exp_date, status=status)

    customer.sync_overall_fields()
    return JsonResponse({"success": True, "student": {"id": customer.id, "full_name": customer.full_name, "customer_email": customer.customer_email}})


@csrf_exempt
@api_login_required
def api_dashboard_delete(request: HttpRequest, id: int) -> JsonResponse:
    customer = get_object_or_404(Customer, id=id)
    email = customer.customer_email
    customer.delete()
    return JsonResponse({"success": True, "message": f"Đã xóa học viên '{email}'."})


@api_login_required
def api_student_detail(request: HttpRequest, id: int) -> JsonResponse:
    student = get_object_or_404(Customer.objects.prefetch_related("enrollments__course__links"), id=id)
    enrollments = []
    for e in student.enrollments.all():
        enrollments.append({
            "course_id": e.course_id,
            "course_name": e.course.name,
            "course_description": e.course.description,
            "web_link": e.course.web_link,
            "links": [{"title": l.title, "url": l.url} for l in e.course.links.all()],
            "registration_date": str(e.registration_date) if e.registration_date else None,
            "expiry_date": str(e.expiry_date) if e.expiry_date else None,
            "status": e.status,
        })

    return JsonResponse({
        "id": student.id,
        "full_name": student.full_name,
        "customer_email": student.customer_email,
        "phone_number": student.phone_number,
        "status": student.status,
        "registration_date": str(student.registration_date) if student.registration_date else None,
        "expiry_date": str(student.expiry_date) if student.expiry_date else None,
        "telegram_chat_id": student.telegram_chat_id,
        "is_verified_telegram": student.is_verified_telegram,
        "created_at": student.created_at.isoformat(),
        "enrollments": enrollments,
    })


@api_login_required
def api_dashboard_stats(request: HttpRequest) -> JsonResponse:
    total = Customer.objects.count()
    active = Customer.objects.filter(status="ACTIVE").count()
    pending = Customer.objects.filter(status="PENDING").count()
    expired = Customer.objects.filter(status="EXPIRED").count()
    total_courses = Course.objects.count()
    voomly_courses = Course.objects.exclude(spotlight_id__isnull=True).exclude(spotlight_id="").count()
    return JsonResponse({
        "total_students": total,
        "active_count": active,
        "pending_count": pending,
        "expired_count": expired,
        "total_courses": total_courses,
        "total_voomly_courses": voomly_courses,
    })


# ─── API: Courses ─────────────────────────────────────────────────────────────

@api_login_required
def api_courses_list(request: HttpRequest) -> JsonResponse:
    page_number = request.GET.get("page", 1)
    qs = Course.objects.annotate(student_count=Count("customers")).order_by("-created_at")
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(page_number)

    courses_data = []
    for c in page_obj:
        courses_data.append({
            "id": c.id,
            "name": c.name,
            "spotlight_id": c.spotlight_id or "",
            "description": c.description or "",
            "web_link": c.web_link or "",
            "student_count": c.student_count,
            "created_at": c.created_at.isoformat(),
        })

    return JsonResponse({
        "courses": courses_data,
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
def api_courses_create(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    name = data.get("name", "").strip()
    if not name:
        return JsonResponse({"error": "Tên khóa học không được để trống."}, status=400)

    course = Course.objects.create(
        name=name,
        spotlight_id=data.get("spotlight_id", "").strip() or None,
        description=data.get("description", "").strip(),
        web_link=data.get("web_link", "").strip(),
    )
    for link in data.get("links", []):
        title = link.get("title", "").strip()
        url = link.get("url", "").strip()
        if title and url:
            CourseLink.objects.create(course=course, title=title, url=url)

    return JsonResponse({"success": True, "course": {"id": course.id, "name": course.name}})


@csrf_exempt
@api_login_required
def api_courses_update(request: HttpRequest, id: int) -> JsonResponse:
    if request.method != "PUT":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    course = get_object_or_404(Course, id=id)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if data.get("name"):
        course.name = data["name"].strip()
    course.spotlight_id = data.get("spotlight_id", "").strip() or None
    course.description = data.get("description", "").strip()
    course.web_link = data.get("web_link", "").strip()
    course.save()

    course.links.all().delete()
    for link in data.get("links", []):
        title = link.get("title", "").strip()
        url = link.get("url", "").strip()
        if title and url:
            CourseLink.objects.create(course=course, title=title, url=url)

    return JsonResponse({"success": True, "course": {"id": course.id, "name": course.name}})


@csrf_exempt
@api_login_required
def api_courses_delete(request: HttpRequest, id: int) -> JsonResponse:
    course = get_object_or_404(Course, id=id)
    name = course.name
    course.delete()
    return JsonResponse({"success": True, "message": f"Đã xóa khóa học '{name}'."})


@api_login_required
def api_course_detail_json(request: HttpRequest, id: int) -> JsonResponse:
    course = get_object_or_404(Course, id=id)
    student_count = Enrollment.objects.filter(course=course).count()
    links_data = [{"title": l.title, "url": l.url} for l in course.links.all()]

    voomly_students = []
    voomly_error = ""
    if course.spotlight_id:
        try:
            voomly_students = fetch_students_for_course(course)
        except Exception as exc:
            voomly_error = str(exc)

    return JsonResponse({
        "course": {
            "id": course.id,
            "name": course.name,
            "spotlight_id": course.spotlight_id or "",
            "description": course.description or "",
            "web_link": course.web_link or "",
            "links": links_data,
            "created_at": course.created_at.isoformat(),
        },
        "student_count": student_count,
        "voomly_students": voomly_students,
        "voomly_error": voomly_error,
    })


# ─── API: Enroll ──────────────────────────────────────────────────────────────

@csrf_exempt
@api_login_required
def api_enroll_student(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    course_id = data.get("course_id")
    student_id = data.get("student_id")
    course = get_object_or_404(Course, id=course_id)

    today = timezone.localdate()
    reg_date = _parse_date(data.get("registration_date")) or today
    exp_date = _parse_date(data.get("expiry_date")) or (reg_date + timedelta(days=365))
    status = data.get("status", "ACTIVE")

    if student_id:
        student = get_object_or_404(Customer, id=student_id)
    else:
        email = data.get("customer_email", "").strip().lower()
        if not email:
            return JsonResponse({"error": "Email học viên không được để trống."}, status=400)
        full_name = data.get("full_name", "").strip()
        phone = normalize_phone_number(data.get("phone_number", ""))
        student, _ = Customer.objects.get_or_create(
            customer_email=email,
            defaults={"full_name": full_name, "phone_number": phone},
        )

    enrollment, created = Enrollment.objects.update_or_create(
        customer=student,
        course=course,
        defaults={"registration_date": reg_date, "expiry_date": exp_date, "status": status},
    )
    student.sync_overall_fields()

    voomly_synced = False
    if course.spotlight_id:
        success = add_student_to_voomly(
            course=course,
            name=student.full_name or "Học viên",
            email=student.customer_email,
            phone=student.phone_number or "",
        )
        if success:
            wait_for_voomly_student(course, student.customer_email)
            voomly_synced = True

    return JsonResponse({
        "success": True,
        "enrollment": {
            "id": enrollment.id,
            "course_id": enrollment.course_id,
            "customer_id": enrollment.customer_id,
            "registration_date": str(enrollment.registration_date),
            "expiry_date": str(enrollment.expiry_date),
            "status": enrollment.status,
            "created": created,
        },
        "voomly_synced": voomly_synced,
    })


# ─── API: Sync ────────────────────────────────────────────────────────────────

@csrf_exempt
@api_login_required
def api_sync_courses(request: HttpRequest) -> JsonResponse:
    try:
        result = sync_courses_from_voomly()
        return JsonResponse({"success": True, "result": result})
    except Exception as e:
        return JsonResponse({"error": f"Lỗi đồng bộ khóa học: {e}"}, status=500)


@csrf_exempt
@api_login_required
def api_sync_students(request: HttpRequest) -> JsonResponse:
    try:
        result = sync_all_students_from_voomly()
        return JsonResponse({"success": True, "result": result})
    except Exception as e:
        return JsonResponse({"error": f"Lỗi đồng bộ học viên: {e}"}, status=500)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _parse_date(value: str | None):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None
