import email
import imaplib
import logging
import re
import time
from datetime import timedelta
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime
from typing import Iterable

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Course, Customer


EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
logger = logging.getLogger(__name__)
COURSE_NAMES = [
    "ChatGPT Automation",
    "Prompt Engineering Basic",
    "AI Support Agent",
    "Python for Office",
    "Email Workflow Mastery",
]
FALLBACK_NAMES = [
    "Nguyen Minh Anh",
    "Tran Quoc Dat",
    "Le Hoang Nam",
    "Pham Gia Han",
    "Vo Thanh Tung",
]


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.fullmatch(email.strip()))


def list_available_courses() -> list[Course]:
    return list(Course.objects.order_by("name"))


def normalize_phone_number(phone_number: str) -> str:
    return re.sub(r"\D+", "", phone_number or "")


def _build_customer_profile(chat_id: int, customer_email: str) -> dict[str, object]:
    seed = abs(chat_id) + sum(ord(char) for char in customer_email.lower())
    local_part = customer_email.split("@", 1)[0]
    tokens = [token.capitalize() for token in re.split(r"[._-]+", local_part) if token and token.isalpha()]
    full_name = " ".join(tokens[:4]) if tokens else FALLBACK_NAMES[seed % len(FALLBACK_NAMES)]
    registration_date = timezone.localdate()
    expiry_date = registration_date + timedelta(days=30 + (seed % 90))
    phone_number = f"0{((seed % 900000000) + 100000000):09d}"
    return {
        "full_name": full_name,
        "phone_number": phone_number,
        "registration_date": registration_date,
        "expiry_date": expiry_date,
    }


def _default_course_names(chat_id: int, customer_email: str) -> list[str]:
    seed = abs(chat_id) + sum(ord(char) for char in customer_email.lower())
    first_index = seed % len(COURSE_NAMES)
    second_index = (first_index + 2) % len(COURSE_NAMES)
    if first_index == second_index:
        return [COURSE_NAMES[first_index]]
    return [COURSE_NAMES[first_index], COURSE_NAMES[second_index]]


def create_or_update_customer(chat_id: int, customer_email: str) -> Customer:
    Customer.objects.filter(telegram_chat_id=chat_id).exclude(customer_email=customer_email).delete()
    customer, _ = Customer.objects.update_or_create(
        customer_email=customer_email,
        defaults={
            "telegram_chat_id": chat_id,
            "status": "PENDING",
            "has_sent_otp": False,
        },
    )
    profile_data = _build_customer_profile(chat_id, customer_email)
    fields_to_update = []
    for field_name, value in profile_data.items():
        if not getattr(customer, field_name):
            setattr(customer, field_name, value)
            fields_to_update.append(field_name)
    if fields_to_update:
        customer.save(update_fields=fields_to_update)

    if not customer.courses.exists():
        courses = list(Course.objects.filter(name__in=_default_course_names(chat_id, customer_email)))
        if courses:
            customer.courses.set(courses)
    return customer


def get_or_create_customer_for_otp(customer_email: str, otp_code: str) -> Customer:
    normalized_email = customer_email.strip().lower()
    customer = Customer.objects.filter(customer_email=normalized_email).first()
    if not customer:
        customer = Customer.objects.create(
            customer_email=normalized_email,
            status="PENDING",
            has_sent_otp=False,
            is_verified_telegram=False,
        )
        profile_data = _build_customer_profile(0, normalized_email)
        for field_name, value in profile_data.items():
            setattr(customer, field_name, value)
        customer.save()
        
        courses = list(Course.objects.filter(name__in=_default_course_names(0, normalized_email)))
        if courses:
            customer.courses.set(courses)
            
    customer.telegram_otp = otp_code
    customer.telegram_otp_created_at = timezone.now()
    customer.save(update_fields=["telegram_otp", "telegram_otp_created_at"])
    return customer


def send_telegram_otp_email(to_email: str, otp_code: str) -> bool:
    try:
        context = {
            "purpose": "Xác thực tài khoản Telegram",
            "code": otp_code,
            "expire_minutes": 10,
            "support_email": settings.EMAIL_ACCOUNT,
            "company_name": settings.COMPANY_NAME,
        }
        html_content = render_to_string("otp_email.html", context)
        text_content = render_to_string("otp_email.txt", context)
        
        subject = f"[{settings.COMPANY_NAME}] Mã OTP xác thực Telegram"
        from_email = f"{settings.COMPANY_NAME} <{settings.EMAIL_ACCOUNT}>"
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[to_email.strip()],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logger.info(f"Đã gửi email OTP xác thực Telegram tới {to_email}")
        return True
    except Exception as e:
        logger.exception(f"Lỗi gửi email OTP tới {to_email}: {e}")
        return False


def upsert_customer_from_web(
    *,
    customer_email: str,
    phone_number: str,
    full_name: str,
    course_names: Iterable[str],
    registration_date,
    expiry_date,
    status: str = "ACTIVE",
) -> Customer:
    normalized_phone = normalize_phone_number(phone_number)
    customer, _ = Customer.objects.update_or_create(
        customer_email=customer_email.strip().lower(),
        defaults={
            "phone_number": normalized_phone,
            "full_name": full_name.strip(),
            "registration_date": registration_date,
            "expiry_date": expiry_date,
            "status": status,
        },
    )

    resolved_courses = []
    for course_name in sorted({name.strip() for name in course_names if name and name.strip()}):
        course, _ = Course.objects.get_or_create(name=course_name)
        resolved_courses.append(course)

    customer.courses.set(resolved_courses)
    return customer


def lookup_customers(keyword: str) -> list[Customer]:
    cleaned_keyword = keyword.strip()
    if not cleaned_keyword:
        return []

    normalized_phone = normalize_phone_number(cleaned_keyword)
    filters = (
        Q(customer_email__icontains=cleaned_keyword)
        | Q(full_name__icontains=cleaned_keyword)
        | Q(courses__name__icontains=cleaned_keyword)
    )
    if normalized_phone:
        filters |= Q(phone_number__icontains=normalized_phone)

    return list(
        Customer.objects.filter(filters)
        .prefetch_related("courses")
        .order_by("-created_at")
        .distinct()[:10]
    )


def lookup_customer_by_email(customer_email: str) -> Customer | None:
    normalized_email = customer_email.strip().lower()
    if not normalized_email or not is_valid_email(normalized_email):
        return None

    return (
        Customer.objects.filter(customer_email=normalized_email)
        .prefetch_related("courses", "enrollments__course")
        .first()
    )


def _message_text(msg: email.message.Message) -> str:
    body = ""
    if msg.is_multipart():
        for subpart in msg.walk():
            content_type = subpart.get_content_type()
            disposition = str(subpart.get("Content-Disposition", ""))
            if content_type == "text/plain" and "attachment" not in disposition.lower():
                payload = subpart.get_payload(decode=True) or b""
                body += payload.decode(errors="ignore")
    else:
        payload = msg.get_payload(decode=True) or b""
        body = payload.decode(errors="ignore")
    return body


def _decode_mime_header(value: str) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _is_openai_otp_email(msg: email.message.Message) -> bool:
    sender = _decode_mime_header(str(msg.get("From", ""))).lower()
    subject = _decode_mime_header(str(msg.get("Subject", ""))).lower()
    body = _message_text(msg).lower()

    sender_ok = "tm.openai.com" in sender or "openai.com" in sender
    subject_ok = (
        "mã đăng nhập chatgpt tạm thời của bạn" in subject
        or "ma dang nhap chatgpt tam thoi cua ban" in subject
        or "chatgpt" in subject
    )
    body_ok = (
        "ma xac minh" in body
        or "temporary" in body
        or "verification code" in body
        or "dang nhap" in body
        or "chatgpt" in body
    )
    return sender_ok and (subject_ok or body_ok)


def _message_timestamp(msg: email.message.Message) -> float | None:
    date_header = msg.get("Date")
    if not date_header:
        return None
    try:
        return parsedate_to_datetime(date_header).timestamp()
    except Exception:
        return None


def extract_otp_from_openai_email(
    timeout_seconds: int = 120,
    interval_seconds: int = 5,
    min_received_timestamp: float | None = None,
) -> str | None:
    deadline = time.time() + timeout_seconds
    logger.info(
        "Bat dau quet Gmail OTP. email_account=%s timeout_seconds=%s interval_seconds=%s min_received_timestamp=%s",
        settings.EMAIL_ACCOUNT,
        timeout_seconds,
        interval_seconds,
        min_received_timestamp,
    )

    while time.time() < deadline:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        try:
            mail.login(settings.EMAIL_ACCOUNT, settings.APP_PASSWORD)
            mail.select("inbox")
            status, messages = mail.search(None, '(UNSEEN FROM "openai")')
            if status != "OK" or not messages or not messages[0]:
                status, messages = mail.search(None, '(UNSEEN FROM "tm.openai.com")')
            if status != "OK" or not messages or not messages[0]:
                status, messages = mail.search(None, '(UNSEEN SUBJECT "ChatGPT")')
            if status != "OK" or not messages or not messages[0]:
                status, messages = mail.search(None, '(UNSEEN SUBJECT "OpenAI")')
            logger.info(
                "Ket qua search mail OpenAI. status=%s count=%s",
                status,
                len(messages[0].split()) if status == "OK" and messages and messages[0] else 0,
            )
            if status != "OK" or not messages or not messages[0]:
                time.sleep(interval_seconds)
                continue

            for num in reversed(messages[0].split()):
                _, msg_data = mail.fetch(num, "(RFC822)")
                for part in msg_data:
                    if not isinstance(part, tuple):
                        continue
                    msg = email.message_from_bytes(part[1])
                    sender = _decode_mime_header(str(msg.get("From", "")))
                    subject = _decode_mime_header(str(msg.get("Subject", "")))
                    date_header = str(msg.get("Date", ""))
                    logger.info(
                        "Dang xet mail. seq=%s from=%s subject=%s date=%s",
                        num.decode() if isinstance(num, bytes) else str(num),
                        sender,
                        subject,
                        date_header,
                    )
                    if not _is_openai_otp_email(msg):
                        logger.info("Bo qua mail vi khong khop mau OpenAI OTP.")
                        continue
                    if min_received_timestamp is not None:
                        msg_ts = _message_timestamp(msg)
                        if msg_ts is not None and msg_ts < (min_received_timestamp - 60):
                            logger.info(
                                "Bo qua mail vi qua cu. msg_ts=%s min_received_timestamp=%s",
                                msg_ts,
                                min_received_timestamp,
                            )
                            continue

                    body = _message_text(msg)
                    otp_match = re.search(r"\b\d{6}\b", body)
                    if otp_match:
                        mail.store(num, "+FLAGS", "\\Seen")
                        logger.info(
                            "Tim thay OTP tu mail. seq=%s subject=%s date=%s otp=%s",
                            num.decode() if isinstance(num, bytes) else str(num),
                            subject,
                            date_header,
                            otp_match.group(0),
                        )
                        return otp_match.group(0)
                    logger.info("Mail khop mau OpenAI nhung khong tim thay OTP 6 so.")
        finally:
            try:
                mail.logout()
            except Exception:
                pass

        time.sleep(interval_seconds)

    logger.info("Het thoi gian quet Gmail OTP nhung khong tim thay ma.")
    return None


def mark_customer_otp_received(chat_id: int, customer_email: str) -> None:
    Customer.objects.filter(
        Q(telegram_chat_id=chat_id) | Q(customer_email=customer_email)
    ).update(status="ACTIVE", has_sent_otp=True)


def sync_courses_from_voomly() -> dict[str, int]:
    import requests
    from django.conf import settings
    from .models import Course, CourseLink
    from django.db import transaction
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    url = "https://api.voomly.com/spotlights?tiny=1"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {settings.VOOMLY_BEARER_TOKEN}",
        "cache-control": "no-cache",
        "funnel-version": "2",
        "origin": "https://app.voomly.com",
        "player-version": "2",
        "pragma": "no-cache",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            raise Exception(f"Voomly API returned status {response.status_code}: {response.text[:200]}")
            
        spotlights = response.json()
        if not isinstance(spotlights, list):
            raise Exception("Invalid API response format: expected a list of spotlights.")
            
        created_count = 0
        updated_count = 0
        
        # 1. Sync courses and spotlight_ids from list API
        for spotlight in spotlights:
            spotlight_id = spotlight.get("id")
            name = spotlight.get("name")
            if not spotlight_id or not name:
                continue
                
            name = name.strip()
            
            # Case 1: Course with this spotlight_id already exists
            course = Course.objects.filter(spotlight_id=spotlight_id).first()
            if course:
                if course.name != name:
                    course.name = name
                    course.save(update_fields=["name"])
                    updated_count += 1
                continue
                
            # Case 2: Course with same name exists but doesn't have spotlight_id
            course = Course.objects.filter(name__iexact=name).first()
            if course:
                course.spotlight_id = spotlight_id
                course.save(update_fields=["spotlight_id"])
                updated_count += 1
                continue
                
            # Case 3: Create new course
            Course.objects.create(
                spotlight_id=spotlight_id,
                name=name
            )
            created_count += 1
            
        # 2. Xóa sạch link web khoá học hiện có và các bản ghi trong bảng CourseLink
        Course.objects.all().update(web_link="")
        CourseLink.objects.all().delete()
        
        # 3. Lấy trường id khoá học (spotlight_id) trong database để gọi API chi tiết
        courses_with_id = list(Course.objects.exclude(spotlight_id__isnull=True).exclude(spotlight_id=""))
        
        # Helper to fetch customDomain from single spotlight API
        def fetch_domain(c):
            import requests
            detail_url = f"https://api.voomly.com/spotlights/{c.spotlight_id}"
            try:
                res = requests.get(detail_url, headers=headers, timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    cd = data.get("customDomain")
                    if cd:
                        cd = cd.strip()
                        if not (cd.startswith("http://") or cd.startswith("https://")):
                            return c.id, f"https://{cd}"
                        return c.id, cd
            except Exception as err:
                logger.error(f"Error fetching customDomain for course {c.name} ({c.spotlight_id}): {err}")
            return c.id, ""

        # Fetch customDomain in parallel using ThreadPoolExecutor
        course_domains = {}
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = {executor.submit(fetch_domain, c): c for c in courses_with_id}
            for future in as_completed(futures):
                c_id, web_link = future.result()
                if web_link:
                    course_domains[c_id] = web_link
                    
        # 4. Cập nhật các web_link thu được vào database
        with transaction.atomic():
            for c in courses_with_id:
                new_link = course_domains.get(c.id, "")
                if new_link:
                    c.web_link = new_link
                    c.save(update_fields=["web_link"])
            
        return {
            "total": len(spotlights),
            "created": created_count,
            "updated": updated_count,
        }
    except requests.RequestException as e:
        raise Exception(f"Network error when calling Voomly API: {e}")


def fetch_students_for_course(course: Course) -> list[dict]:
    import requests
    from django.conf import settings
    from django.utils.dateparse import parse_datetime
    from datetime import datetime, timedelta
    from django.utils import timezone

    if not course.spotlight_id:
        logger.info(f"[Voomly] fetch_students_for_course: course '{course.name}' (id={course.id}) không có spotlight_id, bỏ qua.")
        return []

    logger.info(f"[Voomly] fetch_students_for_course: BẮT ĐẦU tải học viên cho course='{course.name}' spotlight_id={course.spotlight_id}")
    url = f"https://api.voomly.com/spotlights/{course.spotlight_id}/customers"
    params = {
        "startTime": "1970-01-01T07:00:00",
        "endTime": timezone.localtime().strftime("%Y-%m-%dT%H:%M:%S"),
        "timeZone": "Etc/GMT-7",
        "skip": 0,
        "limit": 100,
        "sortField": "createdAt",
        "sortDirection": "desc"
    }
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {settings.VOOMLY_BEARER_TOKEN}",
        "cache-control": "no-cache",
        "funnel-version": "2",
        "origin": "https://app.voomly.com",
        "player-version": "2",
        "pragma": "no-cache",
    }

    # Check token
    token_preview = settings.VOOMLY_BEARER_TOKEN[:10] + "..." if settings.VOOMLY_BEARER_TOKEN else "(EMPTY)"
    logger.info(f"[Voomly] URL={url} | VOOMLY_BEARER_TOKEN={token_preview} | startTime={params['startTime']} | endTime={params['endTime']}")

    students = []
    skip = 0
    limit = 100
    first_request = True

    try:
        while True:
            params["skip"] = skip
            params["limit"] = limit
            logger.info(f"[Voomly] Request: GET {url} với skip={skip} limit={limit}")
            response = requests.get(url, headers=headers, params=params, timeout=15)
            logger.info(f"[Voomly] Response status={response.status_code} cho skip={skip}")

            if response.status_code != 200:
                error_msg = f"Voomly API lỗi (status={response.status_code}) khi tải học viên cho khóa học '{course.name}': {response.text[:300]}"
                logger.error(error_msg)
                if first_request:
                    raise Exception(error_msg)
                break
            first_request = False

            data = response.json()
            items = data.get("items", [])
            logger.info(f"[Voomly] Response body chứa {len(items)} items (type={type(items).__name__})")

            if not isinstance(items, list) or not items:
                logger.info(f"[Voomly] Hết dữ liệu hoặc items rỗng, dừng phân trang.")
                break

            for item in items:
                email = item.get("email", "").strip().lower()
                name = item.get("name", "").strip()
                status_raw = item.get("status", "")
                created_at_str = item.get("createdAt", "")

                if not email:
                    logger.warning(f"[Voomly] Bỏ qua item thiếu email: name={name}")
                    continue

                # Parse registration date
                reg_date = None
                if created_at_str:
                    dt = parse_datetime(created_at_str)
                    if dt:
                        reg_date = dt.date()
                if not reg_date:
                    reg_date = timezone.localdate()

                expiry_date = reg_date + timedelta(days=365) # Default 1 year expiry

                # Map Voomly status to our Customer status
                status = "ACTIVE" if status_raw == "complete" else "PENDING"

                students.append({
                    "email": email,
                    "name": name,
                    "registration_date": reg_date,
                    "expiry_date": expiry_date,
                    "status": status,
                })

            logger.info(f"[Voomly] Lũy kế: {len(students)} học viên sau skip={skip}")

            if len(items) < limit:
                logger.info(f"[Voomly] items ({len(items)}) < limit ({limit}), dừng phân trang.")
                break

            skip += limit

        logger.info(f"[Voomly] KẾT THÚC: tổng cộng {len(students)} học viên cho course '{course.name}'")
        return students
    except Exception as e:
        logger.error(f"[Voomly] Network error when fetching students for course {course.name}: {e}")
        if first_request:
            raise
        return students


def wait_for_voomly_student(course: Course, customer_email: str, attempts: int = 6, delay_seconds: int = 2) -> list[dict]:
    target_email = (customer_email or "").strip().lower()
    latest_students = []

    for attempt in range(max(attempts, 1)):
        try:
            latest_students = fetch_students_for_course(course)
        except Exception as exc:
            logger.warning(f"Attempt {attempt + 1}/{attempts}: fetch_students_for_course failed: {exc}")
            latest_students = []
        if any((student.get("email") or "").strip().lower() == target_email for student in latest_students):
            return latest_students
        if attempt < attempts - 1:
            time.sleep(delay_seconds)

    return latest_students



def sync_students_for_course(course: Course) -> int:
    from django.db import transaction
    from botapp.models import Customer, Enrollment

    students = fetch_students_for_course(course)
    if not students:
        return 0

    count = 0
    with transaction.atomic():
        for s in students:
            email = s["email"]
            name = s["name"]
            reg_date = s["registration_date"]
            expiry_date = s["expiry_date"]
            status = s["status"]

            customer, created = Customer.objects.get_or_create(
                customer_email=email,
                defaults={
                    "full_name": name,
                    "registration_date": reg_date,
                    "expiry_date": expiry_date,
                    "status": status,
                }
            )

            if not created:
                updated_fields = []
                if not customer.full_name and name:
                    customer.full_name = name
                    updated_fields.append("full_name")
                if updated_fields:
                    customer.save(update_fields=updated_fields)

            Enrollment.objects.update_or_create(
                customer=customer,
                course=course,
                defaults={
                    "registration_date": reg_date,
                    "expiry_date": expiry_date,
                    "status": status,
                }
            )

            customer.sync_overall_fields()
            count += 1

    return count


def sync_all_students_from_voomly() -> dict[str, int]:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from .models import Course, Customer, Enrollment
    from django.db import transaction

    courses = Course.objects.exclude(spotlight_id__isnull=True).exclude(spotlight_id="")
    
    # 1. Fetch all student records from Voomly in parallel (No DB operations inside threads to avoid deadlocks & connection exhaust)
    course_to_students = {}
    with ThreadPoolExecutor(max_workers=15) as executor:
        future_to_course = {executor.submit(fetch_students_for_course, course): course for course in courses}
        for future in as_completed(future_to_course):
            course = future_to_course[future]
            try:
                students = future.result()
                if students:
                    course_to_students[course] = students
            except Exception as exc:
                logger.error(f"Course {course.name} generated an exception during fetch: {exc}")

    total_students_synced = 0
    courses_synced_count = 0

    if not course_to_students:
        return {
            "total_students": 0,
            "courses_count": 0,
        }

    # 2. Sync fetched data into the database in the main thread using bulk operations
    all_emails = set()
    for students in course_to_students.values():
        for student in students:
            all_emails.add(student["email"])

    with transaction.atomic():
        # Get all existing customers with these emails
        existing_customers = {
            cust.customer_email: cust 
            for cust in Customer.objects.filter(customer_email__in=all_emails)
        }

        # Check which customers need to be created
        new_customers_to_create = []
        customers_to_update_name = []
        
        seen_emails_for_create = set()
        for course, students in course_to_students.items():
            for s in students:
                email = s["email"]
                name = s["name"]
                reg_date = s["registration_date"]
                expiry_date = s["expiry_date"]
                status = s["status"]
                
                customer = existing_customers.get(email)
                if not customer:
                    if email not in seen_emails_for_create:
                        new_customers_to_create.append(
                            Customer(
                                customer_email=email,
                                full_name=name,
                                registration_date=reg_date,
                                expiry_date=expiry_date,
                                status=status,
                            )
                        )
                        seen_emails_for_create.add(email)
                else:
                    if not customer.full_name and name:
                        customer.full_name = name
                        if customer not in customers_to_update_name:
                            customers_to_update_name.append(customer)

        # Bulk create new customers
        if new_customers_to_create:
            Customer.objects.bulk_create(new_customers_to_create, ignore_conflicts=True)
            # Re-fetch to get all customers (including newly created ones) with their correct database IDs
            existing_customers = {
                cust.customer_email: cust 
                for cust in Customer.objects.filter(customer_email__in=all_emails)
            }

        # Bulk update customer names if needed
        if customers_to_update_name:
            Customer.objects.bulk_update(customers_to_update_name, fields=["full_name"])

        # Get all existing Enrollments for these customers
        existing_enrollments = {
            (e.customer_id, e.course_id): e
            for e in Enrollment.objects.filter(customer__customer_email__in=all_emails)
        }

        enrolls_to_create = []
        enrolls_to_update = []

        for course, students in course_to_students.items():
            course_synced = False
            for s in students:
                email = s["email"]
                reg_date = s["registration_date"]
                expiry_date = s["expiry_date"]
                status = s["status"]

                customer = existing_customers.get(email)
                if not customer:
                    continue  # Should not happen
                
                key = (customer.id, course.id)
                enroll = existing_enrollments.get(key)
                if not enroll:
                    enrolls_to_create.append(
                        Enrollment(
                            customer=customer,
                            course=course,
                            registration_date=reg_date,
                            expiry_date=expiry_date,
                            status=status
                        )
                    )
                    course_synced = True
                    total_students_synced += 1
                else:
                    changed = False
                    if enroll.registration_date != reg_date:
                        enroll.registration_date = reg_date
                        changed = True
                    if enroll.expiry_date != expiry_date:
                        enroll.expiry_date = expiry_date
                        changed = True
                    if enroll.status != status:
                        enroll.status = status
                        changed = True
                    
                    if changed:
                        enrolls_to_update.append(enroll)
                    
                    course_synced = True
                    total_students_synced += 1

            if course_synced:
                courses_synced_count += 1

        # Bulk create enrollments
        if enrolls_to_create:
            Enrollment.objects.bulk_create(enrolls_to_create)

        # Bulk update enrollments
        if enrolls_to_update:
            Enrollment.objects.bulk_update(enrolls_to_update, fields=["registration_date", "expiry_date", "status"])

        # 3. Bulk update the overall aggregate fields for affected customers
        affected_customer_ids = {cust.id for cust in existing_customers.values() if cust.id}
        if affected_customer_ids:
            # Re-fetch enrollments to get the latest updated values for calculation
            enrollments = Enrollment.objects.filter(customer_id__in=affected_customer_ids)
            from collections import defaultdict
            customer_to_enrolls = defaultdict(list)
            for enroll in enrollments:
                customer_to_enrolls[enroll.customer_id].append(enroll)

            customers_to_bulk_update = []
            for cust_id in affected_customer_ids:
                customer = existing_customers.get(
                    # Find by email using cust_id
                    next((email for email, c in existing_customers.items() if c.id == cust_id), None)
                )
                if not customer:
                    continue
                enrolls = customer_to_enrolls.get(cust_id, [])
                if not enrolls:
                    continue

                reg_dates = [e.registration_date for e in enrolls if e.registration_date]
                new_reg_date = min(reg_dates) if reg_dates else None

                exp_dates = [e.expiry_date for e in enrolls if e.expiry_date]
                new_exp_date = max(exp_dates) if exp_dates else None

                statuses = [e.status for e in enrolls]
                if "ACTIVE" in statuses:
                    new_status = "ACTIVE"
                elif "PENDING" in statuses:
                    new_status = "PENDING"
                else:
                    new_status = "EXPIRED"

                changed = False
                if customer.registration_date != new_reg_date:
                    customer.registration_date = new_reg_date
                    changed = True
                if customer.expiry_date != new_exp_date:
                    customer.expiry_date = new_exp_date
                    changed = True
                if customer.status != new_status:
                    customer.status = new_status
                    changed = True

                if changed:
                    customers_to_bulk_update.append(customer)

            if customers_to_bulk_update:
                Customer.objects.bulk_update(
                    customers_to_bulk_update,
                    fields=["registration_date", "expiry_date", "status"]
                )

    return {
        "total_students": total_students_synced,
        "courses_count": courses_synced_count,
    }


def add_student_to_voomly(course: Course, name: str, email: str, phone: str = "") -> bool:
    """
    Registers a student to Voomly via POST https://api.voomly.com/spotlights/{spotlight_id}/customers
    Returns True if successfully enrolled (or if the account already exists).
    """
    import requests
    from django.conf import settings
    
    if not course.spotlight_id:
        logger.warning(f"Course {course.name} does not have a spotlight_id. Skipping Voomly registration.")
        return False
        
    url = f"https://api.voomly.com/spotlights/{course.spotlight_id}/customers"
    payload = {
        "name": name or "Học viên",
        "email": email.strip().lower(),
        "password": "123456",  # Default password
        "amount": 12300,       # Default amount in cents ($123.00)
        "currency": "usd",
        "comment": f"Tạo tự động — Skill add_student_voomly | {course.name}",
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {settings.VOOMLY_BEARER_TOKEN}",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "origin": "https://app.voomly.com",
        "funnel-version": "2",
        "player-version": "2",
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        # 200 OK or 201 Created or 403 (with SPOTLIGHT_ACCOUNT_ALREADY_EXISTS code)
        if response.status_code in (200, 201):
            logger.info(f"Successfully registered student {email} to Voomly course {course.name}")
            return True
        elif response.status_code == 403:
            try:
                resp_data = response.json()
                if resp_data.get("code") == "SPOTLIGHT_ACCOUNT_ALREADY_EXISTS":
                    logger.info(f"Student {email} already enrolled in Voomly course {course.name}")
                    return True
            except Exception:
                pass
            logger.error(f"Voomly registration error (403): {response.text}")
            return False
        else:
            logger.error(f"Voomly API returned status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error registering student to Voomly: {e}")
        return False
