import email
import html
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

from .models import Course, Customer, ChatGPTAccount


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


def create_customer_from_admin(customer_email: str) -> tuple[Customer, bool]:
    normalized_email = customer_email.strip().lower()
    customer = Customer.objects.filter(customer_email=normalized_email).first()
    created = False

    if not customer:
        customer = Customer.objects.create(
            customer_email=normalized_email,
            status="ACTIVE",
            has_sent_otp=False,
            is_verified_telegram=False,
        )
        profile_data = _build_customer_profile(0, normalized_email)
        for field_name, value in profile_data.items():
            setattr(customer, field_name, value)
        customer.save()
        created = True

    if not customer.courses.exists():
        courses = list(Course.objects.filter(name__in=_default_course_names(0, normalized_email)))
        if courses:
            customer.courses.set(courses)

    if customer.status != "ACTIVE":
        customer.status = "ACTIVE"
        customer.save(update_fields=["status"])

    return customer, created


def assign_courses_to_customer_from_admin(
    customer_email: str,
    course_ids: list[int],
    full_name: str = None,
    phone_number: str = None,
) -> tuple[Customer, bool]:
    customer, created = create_customer_from_admin(customer_email)
    
    # Update full_name and phone_number if they are provided
    updated_fields = []
    if full_name:
        customer.full_name = full_name.strip()
        updated_fields.append("full_name")
    if phone_number:
        customer.phone_number = normalize_phone_number(phone_number)
        updated_fields.append("phone_number")
    if updated_fields:
        customer.save(update_fields=updated_fields)

    normalized_ids = sorted({int(course_id) for course_id in course_ids})
    today = timezone.localdate()
    expiry_date = today + timedelta(days=90)

    Enrollment = customer.enrollments.model
    existing_enrollments = {enrollment.course_id: enrollment for enrollment in customer.enrollments.all()}

    for course_id in normalized_ids:
        enrollment = existing_enrollments.get(course_id)
        if enrollment:
            enrollment.status = "ACTIVE"
            enrollment.registration_date = enrollment.registration_date or today
            enrollment.expiry_date = enrollment.expiry_date or expiry_date
            enrollment.save(update_fields=["status", "registration_date", "expiry_date"])
        else:
            Enrollment.objects.create(
                customer=customer,
                course_id=course_id,
                status="ACTIVE",
                registration_date=today,
                expiry_date=expiry_date,
            )

    Enrollment.objects.filter(customer=customer).exclude(course_id__in=normalized_ids).delete()
    customer.sync_overall_fields()
    return customer, created


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
    def _html_to_text(content: str) -> str:
        cleaned = re.sub(r"<!--.*?-->", " ", content, flags=re.DOTALL)
        cleaned = re.sub(r"<(script|style|head|title)\b[^>]*>.*?</\1>", " ", cleaned, flags=re.IGNORECASE | re.DOTALL)
        cleaned = re.sub(r"<br\s*/?>", "\n", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"</(p|div|tr|td|li|h1|h2|h3|h4|h5|h6)>", "\n", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        cleaned = html.unescape(cleaned)
        cleaned = re.sub(r"[ \t\r\f\v]+", " ", cleaned)
        cleaned = re.sub(r"\n\s*\n+", "\n", cleaned)
        return cleaned.strip()

    body = ""
    html_body = ""
    if msg.is_multipart():
        for subpart in msg.walk():
            content_type = subpart.get_content_type()
            disposition = str(subpart.get("Content-Disposition", ""))
            if content_type == "text/plain" and "attachment" not in disposition.lower():
                payload = subpart.get_payload(decode=True) or b""
                body += payload.decode(errors="ignore")
            elif content_type == "text/html" and "attachment" not in disposition.lower():
                payload = subpart.get_payload(decode=True) or b""
                html_body += payload.decode(errors="ignore")
    else:
        payload = msg.get_payload(decode=True) or b""
        body = payload.decode(errors="ignore")
        if msg.get_content_type() == "text/html":
            html_body = body
            body = ""
    if body.strip():
        return body
    if html_body.strip():
        return _html_to_text(html_body)
    return body


def _extract_otp_from_body(body: str) -> str | None:
    if not body:
        return None

    prioritized_patterns = [
        r"(?:mã xác minh tạm thời|ma xac minh tam thoi)[^\d]{0,80}(\d{6})",
        r"(?:mã xác minh|ma xac minh)[^\d]{0,80}(\d{6})",
        r"(?:verification code|temporary code)[^\d]{0,80}(\d{6})",
        r"(?:continue|tiếp tục)[^\d]{0,80}(\d{6})",
    ]
    for pattern in prioritized_patterns:
        match = re.search(pattern, body, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1)

    lines = [line.strip() for line in body.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        if re.fullmatch(r"\d{6}", line):
            nearby = " ".join(lines[max(0, index - 2): min(len(lines), index + 3)]).lower()
            if any(
                keyword in nearby
                for keyword in ["xác minh", "xac minh", "verification", "chatgpt", "openai", "tiếp tục", "continue"]
            ):
                return line

    fallback = re.search(r"\b\d{6}\b", body)
    if fallback:
        return fallback.group(0)
    return None


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


def extract_otp_from_account_email(
    account: ChatGPTAccount,
    timeout_seconds: int = 120,
    interval_seconds: int = 5,
    min_received_timestamp: float | None = None,
) -> str | None:
    deadline = time.time() + timeout_seconds
    imap_user = account.imap_user if account.imap_user else account.email
    logger.info(
        "Bat dau quet Gmail OTP cho ChatGPTAccount. email_account=%s imap_host=%s timeout_seconds=%s interval_seconds=%s min_received_timestamp=%s",
        account.email,
        account.imap_host,
        timeout_seconds,
        interval_seconds,
        min_received_timestamp,
    )

    effective_min_timestamp = min_received_timestamp
    if effective_min_timestamp is None:
        effective_min_timestamp = time.time() - 180

    while time.time() < deadline:
        try:
            mail = imaplib.IMAP4_SSL(account.imap_host, account.imap_port)
        except Exception as e:
            logger.error("Loi ket noi IMAP den %s: %s", account.imap_host, e)
            time.sleep(interval_seconds)
            continue
        try:
            mail.login(imap_user, account.imap_password)
            mail.select("inbox")
            status, messages = mail.search(None, '(UNSEEN FROM "openai")')
            if status != "OK" or not messages or not messages[0]:
                status, messages = mail.search(None, '(UNSEEN FROM "tm.openai.com")')
            if status != "OK" or not messages or not messages[0]:
                status, messages = mail.search(None, '(UNSEEN SUBJECT "ChatGPT")')
            if status != "OK" or not messages or not messages[0]:
                status, messages = mail.search(None, '(UNSEEN SUBJECT "OpenAI")')
            logger.info(
                "Ket qua search mail OpenAI cho %s. status=%s count=%s",
                account.email,
                status,
                len(messages[0].split()) if status == "OK" and messages and messages[0] else 0,
            )
            if status != "OK" or not messages or not messages[0]:
                time.sleep(interval_seconds)
                continue

            candidates: list[tuple[float, bytes | str, str, str, str]] = []
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
                    msg_ts = _message_timestamp(msg)
                    if effective_min_timestamp is not None:
                        if msg_ts is not None and msg_ts < (effective_min_timestamp - 60):
                            logger.info(
                                "Bo qua mail vi qua cu. msg_ts=%s min_received_timestamp=%s",
                                msg_ts,
                                effective_min_timestamp,
                            )
                            continue

                    body = _message_text(msg)
                    otp_code = _extract_otp_from_body(body)
                    if otp_code:
                        candidates.append((
                            msg_ts if msg_ts is not None else 0.0,
                            num,
                            subject,
                            date_header,
                            otp_code,
                        ))
                        logger.info(
                            "Tim thay OTP candidate. seq=%s subject=%s date=%s otp=%s",
                            num.decode() if isinstance(num, bytes) else str(num),
                            subject,
                            date_header,
                            otp_code,
                        )
                        continue
                    logger.info("Mail khop mau OpenAI nhung khong tim thay OTP 6 so.")

            if candidates:
                latest_ts, latest_num, latest_subject, latest_date, latest_otp = max(candidates, key=lambda item: item[0])
                mail.store(latest_num, "+FLAGS", "\\Seen")
                logger.info(
                    "Chon OTP moi nhat. seq=%s subject=%s date=%s ts=%s otp=%s",
                    latest_num.decode() if isinstance(latest_num, bytes) else str(latest_num),
                    latest_subject,
                    latest_date,
                    latest_ts,
                    latest_otp,
                )
                return latest_otp
        except Exception as e:
            logger.exception("Loi xay ra khi doc mail tu tai khoan %s: %s", account.email, e)
        finally:
            try:
                mail.logout()
            except Exception:
                pass

        time.sleep(interval_seconds)

    logger.info("Het thoi gian quet Gmail OTP cho tai khoan %s nhung khong tim thay ma.", account.email)
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

    effective_min_timestamp = min_received_timestamp
    if effective_min_timestamp is None:
        effective_min_timestamp = time.time() - 180

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

            candidates: list[tuple[float, bytes | str, str, str, str]] = []
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
                    msg_ts = _message_timestamp(msg)
                    if effective_min_timestamp is not None:
                        if msg_ts is not None and msg_ts < (effective_min_timestamp - 60):
                            logger.info(
                                "Bo qua mail vi qua cu. msg_ts=%s min_received_timestamp=%s",
                                msg_ts,
                                effective_min_timestamp,
                            )
                            continue

                    body = _message_text(msg)
                    otp_code = _extract_otp_from_body(body)
                    if otp_code:
                        candidates.append((
                            msg_ts if msg_ts is not None else 0.0,
                            num,
                            subject,
                            date_header,
                            otp_code,
                        ))
                        logger.info(
                            "Tim thay OTP candidate. seq=%s subject=%s date=%s otp=%s",
                            num.decode() if isinstance(num, bytes) else str(num),
                            subject,
                            date_header,
                            otp_code,
                        )
                        continue
                    logger.info("Mail khop mau OpenAI nhung khong tim thay OTP 6 so.")

            if candidates:
                latest_ts, latest_num, latest_subject, latest_date, latest_otp = max(candidates, key=lambda item: item[0])
                mail.store(latest_num, "+FLAGS", "\\Seen")
                logger.info(
                    "Chon OTP moi nhat. seq=%s subject=%s date=%s ts=%s otp=%s",
                    latest_num.decode() if isinstance(latest_num, bytes) else str(latest_num),
                    latest_subject,
                    latest_date,
                    latest_ts,
                    latest_otp,
                )
                return latest_otp
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

