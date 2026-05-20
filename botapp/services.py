import email
import imaplib
import logging
import re
import time
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime

from django.conf import settings
from django.db.models import Q

from .models import Customer


EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
logger = logging.getLogger(__name__)


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.fullmatch(email.strip()))


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
    return customer


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
