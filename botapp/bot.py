import logging
import time
from datetime import datetime

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db.models import Prefetch
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from .keyboards import (
    admin_course_selection_keyboard,
    course_list_keyboard,
    enrollment_keyboard,
    main_menu_keyboard,
    restart_keyboard,
    chatgpt_accounts_keyboard,
)
from .services import (
    assign_courses_to_customer_from_admin,
    create_or_update_customer,
    extract_otp_from_openai_email,
    is_valid_email,
    list_available_courses,
    lookup_customer_by_email,
    mark_customer_otp_received,
    get_or_create_customer_for_otp,
    send_telegram_otp_email,
    extract_otp_from_account_email,
)


logger = logging.getLogger(__name__)

ASK_EMAIL = 0
ASK_OTP = 1
ASK_ADMIN_NEW_EMAIL = 2
ASK_ADMIN_COURSES = 3
ASK_ADMIN_NEW_NAME = 4
ASK_ADMIN_NEW_PHONE = 5

ENROLLMENT_STATUS_LABELS = {
    "ACTIVE": "✅ Đang hoạt động",
    "PENDING": "⏳ Chờ xử lý",
    "EXPIRED": "❌ Đã hết hạn",
}


def escape_markdown(text: str) -> str:
    if not text:
        return ""
    for char in ["_", "*", "`", "["]:
        text = text.replace(char, f"\\{char}")
    return text


def _is_admin_customer(customer) -> bool:
    admin_email = (getattr(settings, "EMAIL_ADMIN", "") or "").strip().lower()
    if not admin_email or not customer:
        return False
    return (customer.customer_email or "").strip().lower() == admin_email


def _is_staff_customer(customer) -> bool:
    if not customer:
        return False
    return customer.is_staff or _is_admin_customer(customer)



def _menu_for_customer(customer):
    return main_menu_keyboard(is_admin=_is_staff_customer(customer))


def _admin_course_prompt(email_text: str, name_text: str, phone_text: str, selected_ids: list[int], total_courses: int) -> str:
    return (
        "➕ *Thêm người mới*\n\n"
        f"📧 Email: `{email_text}`\n"
        f"👤 Họ tên: *{escape_markdown(name_text)}*\n"
        f"📞 SĐT: `{phone_text}`\n"
        f"📚 Đã chọn: *{len(selected_ids)} / {total_courses}* khóa học\n\n"
        "Bấm vào khóa học để chọn hoặc bỏ chọn, rồi nhấn *Xác nhận*."
    )


# ─── /start ──────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()

    # Check if user already linked
    chat_id = update.effective_chat.id
    customer = await _find_customer_by_chat_id(chat_id)

    if customer:
        enrollments = await sync_to_async(list)(customer.enrollments.select_related("course").all())
        course_count = len(enrollments)
        role_line = "\n👑 Vai trò: **ADMIN**" if _is_admin_customer(customer) else ""
        await update.message.reply_text(
            f"🎓 *Xin chào {escape_markdown(customer.full_name) or 'bạn'}!*{role_line}\n\n"
            f"📧 `{customer.customer_email}`\n"
            f"📚 *{course_count}* khóa học đang theo dõi\n\n"
            f"Tôi có thể giúp gì cho bạn hôm nay? 👇",
            reply_markup=_menu_for_customer(customer),
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "🎓 *Chào mừng bạn đến với Hệ thống Quản lý Học tập!*\n\n"
        "🤖 Tôi là trợ lý *Thu Nhi* của *Anh Lập Trình*, có thể giúp bạn:\n"
        "• 🔑 Lấy mã OTP OpenAI từ Gmail tự động\n"
        "• 📚 Xem thông tin khóa học đã đăng ký\n"
        "• 📋 Kiểm tra tình trạng học tập\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Để bắt đầu, vui lòng nhập *email* của bạn bên dưới.\n"
        "Ví dụ: `email@example.com`",
        reply_markup=restart_keyboard(),
        parse_mode="Markdown",
    )
    return ASK_EMAIL


# ─── /me ─────────────────────────────────────────────────────────────────────

async def my_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    customer = await _find_customer_by_chat_id(chat_id)
    if not customer:
        await _reply_not_linked(update)
        return

    enrollments = await sync_to_async(list)(customer.enrollments.select_related("course").all())
    course_count = len(enrollments)
    telegram_status = "✅ Đã liên kết" if customer.telegram_chat_id else "❌ Chưa liên kết"
    status_vi = ENROLLMENT_STATUS_LABELS.get(customer.status, customer.status)

    text = (
        f"👤 *Thông tin của bạn*\n\n"
        f"📧 *Email:* `{customer.customer_email}`\n"
        f"👤 *Họ tên:* {escape_markdown(customer.full_name) or 'Chưa cập nhật'}\n"
        f"📞 *SĐT:* {customer.phone_number or 'Chưa cập nhật'}\n"
        f"🔄 *Trạng thái:* {status_vi}\n"
        f"🤖 *Telegram:* {telegram_status}\n"
        f"📚 *Tổng khóa học:* {course_count}"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=_menu_for_customer(customer), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=_menu_for_customer(customer), parse_mode="Markdown")


# ─── /courses ────────────────────────────────────────────────────────────────

async def my_courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    customer = await _find_customer_by_chat_id(chat_id)
    if not customer:
        await _reply_not_linked(update)
        return

    enrollments = await sync_to_async(list)(customer.enrollments.select_related("course").all())
    if not enrollments:
        text = "📚 Bạn chưa đăng ký khóa học nào."
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text, reply_markup=_menu_for_customer(customer))
        else:
            await update.message.reply_text(text, reply_markup=_menu_for_customer(customer))
        return

    course_data = [
        (f"{e.course.name}", e.course_id)
        for e in enrollments
    ]
    page = 0
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "📚 *Khóa học của bạn:*\nChọn khóa học để xem chi tiết.",
            reply_markup=course_list_keyboard(course_data, page),
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "📚 *Khóa học của bạn:*\nChọn khóa học để xem chi tiết.",
            reply_markup=course_list_keyboard(course_data, page),
            parse_mode="Markdown",
        )


# ─── Course detail ───────────────────────────────────────────────────────────

async def course_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    course_id = int(query.data.split("_")[1])

    from .models import Customer, Enrollment
    chat_id = update.effective_chat.id
    customer = await sync_to_async(Customer.objects.filter(telegram_chat_id=chat_id).first)()
    if not customer:
        await query.edit_message_text("Bạn chưa liên kết tài khoản.", reply_markup=restart_keyboard())
        return

    enrollment = await sync_to_async(
        Enrollment.objects.select_related("course").filter(customer=customer, course_id=course_id).first
    )()
    if not enrollment:
        await query.answer("Không tìm thấy khóa học này.", show_alert=True)
        return

    course = enrollment.course
    remaining = ""
    if enrollment.expiry_date:
        days = (enrollment.expiry_date - datetime.now().date()).days
        if days > 0:
            remaining = f"⏳ Còn *{days}* ngày"
        elif days == 0:
            remaining = "⏳ *Hết hạn hôm nay*"
        else:
            remaining = f"❌ Quá hạn *{abs(days)}* ngày"

    text = (
        f"📖 *{escape_markdown(course.name)}*\n\n"
        f"📝 *Mô tả:* {escape_markdown(course.description) or 'Chưa có mô tả'}\n"
        f"📅 *Đăng ký:* {enrollment.registration_date or 'N/A'}\n"
        f"📅 *Hết hạn:* {enrollment.expiry_date or 'N/A'}\n"
        f"📊 *Trạng thái:* {ENROLLMENT_STATUS_LABELS.get(enrollment.status, enrollment.status)}\n"
        f"{remaining}"
    )

    if course.web_link:
        text += f"\n\n🔗 [Website khóa học]({course.web_link})"

    await query.edit_message_text(
        text,
        reply_markup=enrollment_keyboard(),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


# ─── Handle email input ─────────────────────────────────────────────────────

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email_text = update.message.text.strip().lower()

    if not is_valid_email(email_text):
        await update.message.reply_text(
            "❌ Email không hợp lệ. Vui lòng nhập lại email của bạn.",
            reply_markup=restart_keyboard(),
        )
        return ASK_EMAIL

    from .models import Customer
    customer = await sync_to_async(Customer.objects.filter(customer_email=email_text).first)()
    if customer and customer.is_verified_telegram:
        await update.message.reply_text(
            "❌ Email này đã được liên kết thành công với tài khoản Telegram.\n"
            "Bạn không thể yêu cầu gửi lại mã xác thực liên kết nữa.",
            reply_markup=restart_keyboard(),
        )
        return ConversationHandler.END

    import random
    otp_code = f"{random.randint(100000, 999999)}"

    try:
        # Create or update customer record for OTP
        customer = await sync_to_async(get_or_create_customer_for_otp)(email_text, otp_code)
        
        # Send verification OTP email
        email_sent = await sync_to_async(send_telegram_otp_email)(email_text, otp_code)
        if not email_sent:
            raise Exception("Failed to send OTP email.")
    except Exception:
        logger.exception("Không tạo được phiên xác thực hoặc gửi email.")
        await update.message.reply_text(
            "❌ Không gửi được mã xác thực đến email của bạn. Vui lòng kiểm tra lại cấu hình SMTP hoặc thử lại sau.",
            reply_markup=restart_keyboard(),
        )
        return ConversationHandler.END

    context.user_data["pending_email"] = email_text
    context.user_data["otp_attempts"] = 0

    await update.message.reply_text(
        f"🔑 *Đã gửi mã xác thực!*\n\n"
        f"Một mã OTP gồm 6 chữ số đã được gửi đến email: `{email_text}`.\n"
        f"Mã có hiệu lực trong 10 phút. Vui lòng kiểm tra hộp thư và nhập mã OTP vào đây để tiếp tục.",
        reply_markup=restart_keyboard(),
        parse_mode="Markdown",
    )
    return ASK_OTP


async def handle_otp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    otp_text = update.message.text.strip()
    email_text = context.user_data.get("pending_email")
    chat_id = update.effective_chat.id

    if not email_text:
        await update.message.reply_text(
            "❌ Phiên xác thực không hợp lệ. Vui lòng bấm /start để thực hiện lại.",
            reply_markup=restart_keyboard(),
        )
        return ConversationHandler.END

    from .models import Customer
    from django.utils import timezone
    from datetime import timedelta

    customer = await sync_to_async(Customer.objects.filter(customer_email=email_text).first)()
    if not customer:
        await update.message.reply_text(
            "❌ Không tìm thấy thông tin học viên. Vui lòng bấm /start để bắt đầu lại.",
            reply_markup=restart_keyboard(),
        )
        return ConversationHandler.END

    now = timezone.now()
    is_expired = False
    if customer.telegram_otp_created_at:
        expiry_limit = customer.telegram_otp_created_at + timedelta(minutes=10)
        if now > expiry_limit:
            is_expired = True

    if is_expired or not customer.telegram_otp or customer.telegram_otp != otp_text:
        attempts = context.user_data.get("otp_attempts", 0) + 1
        context.user_data["otp_attempts"] = attempts

        if attempts >= 5:
            await update.message.reply_text(
                "❌ Bạn đã nhập sai mã OTP quá nhiều lần. Vui lòng bấm /start để thực hiện lại.",
                reply_markup=restart_keyboard(),
            )
            context.user_data.clear()
            return ConversationHandler.END

        await update.message.reply_text(
            f"❌ Mã OTP không chính xác hoặc đã hết hạn (lần {attempts}/5). Vui lòng thử lại.",
            reply_markup=restart_keyboard(),
        )
        return ASK_OTP

    # Successful verification!
    # 1. Unlink any other customers with this chat_id
    await sync_to_async(
        lambda: Customer.objects.filter(telegram_chat_id=chat_id)
        .exclude(customer_email=email_text)
        .update(telegram_chat_id=None, is_verified_telegram=False)
    )()

    # 2. Update current customer
    customer.telegram_chat_id = chat_id
    customer.is_verified_telegram = True
    customer.telegram_otp = None
    customer.telegram_otp_created_at = None
    if customer.status == "PENDING":
        customer.status = "ACTIVE"
    await sync_to_async(customer.save)()

    context.user_data["email"] = email_text
    context.user_data.pop("pending_email", None)
    context.user_data.pop("otp_attempts", None)

    courses_list = await sync_to_async(list)(customer.courses.all())
    if courses_list:
        max_display = 5
        displayed_courses = courses_list[:max_display]
        assigned_courses = "\n".join(f"• 📖 {escape_markdown(c.name)}" for c in displayed_courses)
        if len(courses_list) > max_display:
            assigned_courses += f"\n• ➕ _và {len(courses_list) - max_display} khóa học khác..._"
    else:
        assigned_courses = "❌ Chưa có khóa học nào."

    await update.message.reply_text(
        f"✅ *Xác thực thành công!*\n\n"
        f"📧 Tài khoản Telegram của bạn đã được liên kết với email `{email_text}`.\n\n"
        f"👤 Họ tên: {customer.full_name or 'Chưa cập nhật'}\n"
        f"📞 SĐT: {customer.phone_number or 'Chưa có SĐT'}\n"
        f"📚 Khóa học của bạn:\n{assigned_courses}\n\n"
        f"Bây giờ bạn đã có thể sử dụng menu bên dưới.",
        reply_markup=_menu_for_customer(customer),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


# ─── Fetch OTP ───────────────────────────────────────────────────────────────

async def fetch_openai_otp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    customer = await _find_customer_by_chat_id(chat_id)
    if customer and _is_staff_customer(customer):
        await show_accounts(update, context, query=query)
        return

    email_text = context.user_data.get("email")

    if not email_text:
        # Try to get email from DB
        if customer:
            email_text = customer.customer_email
            context.user_data["email"] = email_text
        else:
            context.user_data.clear()
            await query.edit_message_text(
                "❌ Phiên xác thực không còn hợp lệ. Vui lòng bấm /start để thử lại.",
                reply_markup=restart_keyboard(),
            )
            return

    context.user_data.setdefault("otp_session_started_at", time.time())
    await query.edit_message_text("🔍 *Đang quét Gmail để tìm OTP OpenAI...*\nVui lòng đợi trong giây lát.", parse_mode="Markdown")
    try:
        otp_code = await sync_to_async(extract_otp_from_openai_email)(
            timeout_seconds=settings.OTP_TTL_MINUTES * 60,
            interval_seconds=5,
            min_received_timestamp=context.user_data.get("otp_session_started_at"),
        )
    except Exception:
        logger.exception("Không đọc được Gmail OpenAI OTP.")
        await query.edit_message_text(
            "❌ Không đọc được Gmail lúc này. Kiểm tra lại EMAIL_ACCOUNT và APP_PASSWORD.",
            reply_markup=restart_keyboard(),
        )
        return

    if not otp_code:
        await query.edit_message_text(
            "⏳ Không tìm thấy OTP OpenAI trong vòng 1 phút.\n"
            "Hãy gửi OTP bên OpenAI rồi bấm nút bên dưới để thử lại.",
            reply_markup=enrollment_keyboard(),
        )
        return

    await sync_to_async(mark_customer_otp_received)(query.message.chat_id, email_text)
    await query.edit_message_text(
        f"🔑 Mã OTP của bạn là: `{otp_code}`\n\n"
        f"Xong rồi! Cảm ơn bạn.",
        reply_markup=_menu_for_customer(await _find_customer_by_chat_id(query.message.chat_id)),
        parse_mode="Markdown",
    )
    context.user_data.clear()


# ─── /lookup ─────────────────────────────────────────────────────────────────

async def lookup_customer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyword = " ".join(context.args).strip()
    if not keyword:
        await update.message.reply_text(
            "Cú pháp: /lookup `<email>` hoặc `<số điện thoại>`\n"
            "Ví dụ: /lookup email@example.com",
            parse_mode="Markdown",
        )
        return

    customer = await sync_to_async(lookup_customer_by_email)(keyword)
    if not customer:
        # Try lookup by phone
        from .services import lookup_customers
        results = await sync_to_async(lookup_customers)(keyword)
        if results:
            customer = results[0]

    if not customer:
        await update.message.reply_text("❌ Không tìm thấy học viên nào.")
        return

    enrollments = await sync_to_async(list)(customer.enrollments.select_related("course").all())
    course_block = "\n".join(
        f"• {escape_markdown(e.course.name)} — {ENROLLMENT_STATUS_LABELS.get(e.status, e.status)}"
        for e in enrollments
    ) if enrollments else "Chưa có khóa học"

    telegram_value = customer.telegram_chat_id if customer.telegram_chat_id else "❌ Chưa liên kết"
    status_vi = ENROLLMENT_STATUS_LABELS.get(customer.status, customer.status)

    if customer.telegram_chat_id:
        telegram_value = f"✅ `{customer.telegram_chat_id}`"

    text = (
        f"👤 *Kết quả tra cứu*\n\n"
        f"📧 *Email:* `{customer.customer_email}`\n"
        f"👤 *Họ tên:* {escape_markdown(customer.full_name) or 'Chưa cập nhật'}\n"
        f"📞 *SĐT:* {customer.phone_number or 'Chưa cập nhật'}\n"
        f"📊 *Trạng thái:* {status_vi}\n"
        f"🤖 *Telegram:* {telegram_value}\n\n"
        f"📚 *Khóa học:*\n{course_block}"
    )

    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /help ────────────────────────────────────────────────────────────────────

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🎓 *Thu Nhi — Trợ lý Anh Lập Trình*\n\n"
        "_Tôi giúp bạn lấy mã OTP OpenAI và quản lý khóa học._\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "*Các lệnh:*\n\n"
        "🏠 /start — Bắt đầu hoặc liên kết tài khoản\n"
        "👤 /me — Xem thông tin cá nhân\n"
        "📚 /courses — Xem danh sách khóa học\n"
        "🔑 /otp — Lấy mã OTP OpenAI nhanh\n"
        "🔗 /unlink — Hủy liên kết Telegram hiện tại để liên kết email khác\n"
        "🔍 /lookup `<email>` — Tra cứu học viên\n"
        "❓ /help — Hướng dẫn này\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "_💡 Mẹo: Sau khi nhập email, bạn có thể dùng menu để thao tác nhanh hơn!_"
    )
    customer = await _find_customer_by_chat_id(update.effective_chat.id)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=_menu_for_customer(customer), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=_menu_for_customer(customer), parse_mode="Markdown")


# ─── /otp ────────────────────────────────────────────────────────────────────

async def admin_add_user_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    customer = await _find_customer_by_chat_id(update.effective_chat.id)
    if not _is_admin_customer(customer):
        text = "❌ Bạn không có quyền dùng tính năng này."
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text, reply_markup=_menu_for_customer(customer))
        else:
            await update.message.reply_text(text, reply_markup=_menu_for_customer(customer))
        return ConversationHandler.END

    context.user_data["admin_add_mode"] = True
    prompt = (
        "➕ *Thêm người mới*\n\n"
        "Nhập email học viên cần thêm.\n"
        "Ví dụ: `quocdattranhuu1606@gmail.com`"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(prompt, reply_markup=restart_keyboard(), parse_mode="Markdown")
    else:
        await update.message.reply_text(prompt, reply_markup=restart_keyboard(), parse_mode="Markdown")
    return ASK_ADMIN_NEW_EMAIL


async def handle_admin_add_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    customer = await _find_customer_by_chat_id(update.effective_chat.id)
    if not _is_admin_customer(customer):
        context.user_data.pop("admin_add_mode", None)
        await update.message.reply_text("❌ Bạn không có quyền dùng tính năng này.")
        return ConversationHandler.END

    email_text = update.message.text.strip().lower()
    if not is_valid_email(email_text):
        await update.message.reply_text(
            "❌ Email không hợp lệ. Vui lòng nhập lại email học viên.",
            reply_markup=restart_keyboard(),
        )
        return ASK_ADMIN_NEW_EMAIL

    context.user_data["admin_new_email"] = email_text
    await update.message.reply_text(
        "➕ *Thêm người mới*\n\n"
        f"📧 Email: `{email_text}`\n\n"
        "Vui lòng nhập *Họ tên* của học viên:",
        reply_markup=restart_keyboard(),
        parse_mode="Markdown",
    )
    return ASK_ADMIN_NEW_NAME


async def handle_admin_add_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    customer = await _find_customer_by_chat_id(update.effective_chat.id)
    if not _is_admin_customer(customer):
        context.user_data.clear()
        await update.message.reply_text("❌ Bạn không có quyền dùng tính năng này.")
        return ConversationHandler.END

    name_text = update.message.text.strip()
    if not name_text:
        await update.message.reply_text(
            "❌ Họ tên không được để trống. Vui lòng nhập lại Họ tên học viên.",
            reply_markup=restart_keyboard(),
        )
        return ASK_ADMIN_NEW_NAME

    context.user_data["admin_new_name"] = name_text
    email_text = context.user_data.get("admin_new_email")
    await update.message.reply_text(
        "➕ *Thêm người mới*\n\n"
        f"📧 Email: `{email_text}`\n"
        f"👤 Họ tên: *{name_text}*\n\n"
        "Vui lòng nhập *Số điện thoại* của học viên:",
        reply_markup=restart_keyboard(),
        parse_mode="Markdown",
    )
    return ASK_ADMIN_NEW_PHONE


async def handle_admin_add_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    customer = await _find_customer_by_chat_id(update.effective_chat.id)
    if not _is_admin_customer(customer):
        context.user_data.clear()
        await update.message.reply_text("❌ Bạn không có quyền dùng tính năng này.")
        return ConversationHandler.END

    phone_text = update.message.text.strip()
    if not phone_text:
        await update.message.reply_text(
            "❌ Số điện thoại không được để trống. Vui lòng nhập lại Số điện thoại học viên.",
            reply_markup=restart_keyboard(),
        )
        return ASK_ADMIN_NEW_PHONE

    context.user_data["admin_new_phone"] = phone_text
    email_text = context.user_data.get("admin_new_email")
    name_text = context.user_data.get("admin_new_name")

    courses = await sync_to_async(list_available_courses)()
    if not courses:
        await update.message.reply_text(
            "❌ Chưa có khóa học nào trong hệ thống để gán cho học viên.",
            reply_markup=_menu_for_customer(customer),
        )
        context.user_data.clear()
        return ConversationHandler.END

    context.user_data["admin_selected_course_ids"] = []
    context.user_data["admin_course_page"] = 0
    await update.message.reply_text(
        _admin_course_prompt(email_text, name_text, phone_text, [], len(courses)),
        reply_markup=admin_course_selection_keyboard(courses, [], page=0),
        parse_mode="Markdown",
    )
    return ASK_ADMIN_COURSES


async def admin_course_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    customer = await _find_customer_by_chat_id(update.effective_chat.id)
    if not _is_admin_customer(customer):
        await query.edit_message_text("❌ Bạn không có quyền dùng tính năng này.")
        return ConversationHandler.END

    email_text = context.user_data.get("admin_new_email")
    name_text = context.user_data.get("admin_new_name")
    phone_text = context.user_data.get("admin_new_phone")
    if not email_text:
        await query.edit_message_text("❌ Phiên thêm người mới không còn hợp lệ.", reply_markup=_menu_for_customer(customer))
        return ConversationHandler.END

    course_id = int(query.data.rsplit("_", 1)[1])
    selected_ids = set(context.user_data.get("admin_selected_course_ids", []))
    if course_id in selected_ids:
        selected_ids.remove(course_id)
    else:
        selected_ids.add(course_id)

    selected_list = sorted(selected_ids)
    context.user_data["admin_selected_course_ids"] = selected_list
    page = context.user_data.get("admin_course_page", 0)
    courses = await sync_to_async(list_available_courses)()
    await query.edit_message_text(
        _admin_course_prompt(email_text, name_text, phone_text, selected_list, len(courses)),
        reply_markup=admin_course_selection_keyboard(courses, selected_list, page=page),
        parse_mode="Markdown",
    )
    return ASK_ADMIN_COURSES


async def admin_course_page_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    customer = await _find_customer_by_chat_id(update.effective_chat.id)
    if not _is_admin_customer(customer):
        await query.edit_message_text("❌ Bạn không có quyền dùng tính năng này.")
        return ConversationHandler.END

    email_text = context.user_data.get("admin_new_email")
    name_text = context.user_data.get("admin_new_name")
    phone_text = context.user_data.get("admin_new_phone")
    if not email_text:
        await query.edit_message_text("❌ Phiên thêm người mới không còn hợp lệ.", reply_markup=_menu_for_customer(customer))
        return ConversationHandler.END

    page = int(query.data.split("_")[3])
    context.user_data["admin_course_page"] = page
    selected_list = context.user_data.get("admin_selected_course_ids", [])
    courses = await sync_to_async(list_available_courses)()
    await query.edit_message_text(
        _admin_course_prompt(email_text, name_text, phone_text, selected_list, len(courses)),
        reply_markup=admin_course_selection_keyboard(courses, selected_list, page=page),
        parse_mode="Markdown",
    )
    return ASK_ADMIN_COURSES


async def admin_course_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    customer = await _find_customer_by_chat_id(update.effective_chat.id)
    if not _is_admin_customer(customer):
        await query.answer("Bạn không có quyền dùng tính năng này.", show_alert=True)
        return ConversationHandler.END

    email_text = context.user_data.get("admin_new_email")
    name_text = context.user_data.get("admin_new_name")
    phone_text = context.user_data.get("admin_new_phone")
    selected_ids = context.user_data.get("admin_selected_course_ids", [])
    if not email_text:
        await query.answer("Phiên thêm người mới không còn hợp lệ.", show_alert=True)
        return ConversationHandler.END
    if not selected_ids:
        await query.answer("Chọn ít nhất 1 khóa học trước khi xác nhận.", show_alert=True)
        return ASK_ADMIN_COURSES

    await query.answer()
    
    # 1. Loading
    await query.edit_message_text(
        "⏳ *Đang tiến hành tạo/cập nhật học viên...*",
        parse_mode="Markdown",
    )
    
    # 2. Save student and local enrollments
    saved_customer, created = await sync_to_async(assign_courses_to_customer_from_admin)(
        email_text,
        selected_ids,
        full_name=name_text,
        phone_number=phone_text,
    )
    
    # Reload enrollments and build report lines
    assigned_courses = await sync_to_async(list)(saved_customer.enrollments.select_related("course").all())
    
    course_lines = []
    for enrollment in assigned_courses:
        c_name = escape_markdown(enrollment.course.name)
        course_lines.append(f"• 📘 {c_name}")
        
    course_block = "\n".join(course_lines)
    action_text = "Đã thêm mới" if created else "Đã cập nhật"
    
    context.user_data.pop("admin_add_mode", None)
    context.user_data.pop("admin_new_email", None)
    context.user_data.pop("admin_new_name", None)
    context.user_data.pop("admin_new_phone", None)
    context.user_data.pop("admin_course_page", None)
    context.user_data.pop("admin_selected_course_ids", None)
    
    await query.edit_message_text(
        f"✅ *{action_text} học viên thành công!*\n\n"
        f"📧 `{saved_customer.customer_email}`\n"
        f"👤 {escape_markdown(saved_customer.full_name) or 'Chưa cập nhật'}\n"
        f"📞 SĐT: `{saved_customer.phone_number or 'Chưa cập nhật'}`\n"
        f"🔄 Trạng thái: {ENROLLMENT_STATUS_LABELS.get(saved_customer.status, saved_customer.status)}\n\n"
        f"📚 *Khóa học đã gán:*\n{course_block}",
        reply_markup=_menu_for_customer(customer),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def admin_course_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    customer = await _find_customer_by_chat_id(update.effective_chat.id)
    context.user_data.pop("admin_add_mode", None)
    context.user_data.pop("admin_new_email", None)
    context.user_data.pop("admin_new_name", None)
    context.user_data.pop("admin_new_phone", None)
    context.user_data.pop("admin_course_page", None)
    context.user_data.pop("admin_selected_course_ids", None)
    await query.edit_message_text(
        "Đã hủy thêm người mới.",
        reply_markup=_menu_for_customer(customer),
    )
    return ConversationHandler.END


async def otp_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    customer = await _find_customer_by_chat_id(chat_id)
    if not customer:
        await _reply_not_linked(update)
        return

    context.user_data["email"] = customer.customer_email
    context.user_data["otp_session_started_at"] = time.time()
    await update.message.reply_text(
        "🔑 Gửi OTP trên trang OpenAI, sau đó bấm nút bên dưới để tôi lấy mã.",
        reply_markup=enrollment_keyboard(),
        parse_mode="Markdown",
    )


async def show_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None) -> None:
    from .models import ChatGPTAccount
    accounts = await sync_to_async(list)(ChatGPTAccount.objects.filter(status="ACTIVE").order_by("email"))
    if not accounts:
        msg = "📋 Không có tài khoản ChatGPT Plus nào đang hoạt động."
        if query:
            await query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    message_text = (
        "📋 *MÃ OTP OPENAI - CHATGPT ACCOUNTS*\n"
        "──────────────────────────────\n"
        "👉 Chọn nút dưới đây để lấy mã OTP tương ứng sau khi yêu cầu gửi mã từ OpenAI."
    )

    reply_markup = chatgpt_accounts_keyboard(accounts)

    if query:
        await query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )


async def accounts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    customer = await _find_customer_by_chat_id(chat_id)
    if not customer or not _is_staff_customer(customer):
        await update.message.reply_text("❌ Bạn không có quyền truy cập chức năng này.")
        return
    await show_accounts(update, context)


async def accounts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    customer = await _find_customer_by_chat_id(chat_id)
    if not customer or not _is_staff_customer(customer):
        await query.edit_message_text("❌ Bạn không có quyền truy cập chức năng này.")
        return
    await show_accounts(update, context, query=query)


async def fetch_chatgpt_otp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    customer = await _find_customer_by_chat_id(chat_id)
    if not customer or not _is_staff_customer(customer):
        await query.edit_message_text("❌ Bạn không có quyền truy cập chức năng này.")
        return

    # Extract account ID
    acc_id = int(query.data.split("_")[3])

    from .models import ChatGPTAccount
    account = await sync_to_async(ChatGPTAccount.objects.filter(id=acc_id).first)()
    if not account:
        await query.edit_message_text("❌ Không tìm thấy thông tin tài khoản ChatGPT này.")
        return

    await query.edit_message_text(
        f"🔍 *Đang quét Gmail của `{account.email}` để tìm OTP OpenAI...*\nVui lòng đợi trong giây lát.",
        parse_mode="Markdown"
    )

    session_started_at = time.time()

    try:
        otp_code = await sync_to_async(extract_otp_from_account_email)(
            account=account,
            timeout_seconds=120,
            interval_seconds=5,
            min_received_timestamp=session_started_at,
        )
    except Exception:
        logger.exception("Không đọc được Gmail OpenAI OTP.")
        await query.edit_message_text(
            f"❌ Không đọc được Gmail của `{account.email}` lúc này. Vui lòng kiểm tra lại cấu hình IMAP hoặc mật khẩu ứng dụng.",
            reply_markup=chatgpt_accounts_keyboard([account], show_back_to_list=True),
        )
        return

    if not otp_code:
        await query.edit_message_text(
            f"⏳ Không tìm thấy OTP OpenAI cho `{account.email}` trong vòng 2 phút.\n"
            "Hãy gửi lại yêu cầu đăng nhập bên OpenAI rồi bấm nút dưới để thử lại.",
            reply_markup=chatgpt_accounts_keyboard([account], show_back_to_list=True),
        )
        return

    await query.edit_message_text(
        f"🔑 Mã OTP của `{account.email}` là:\n\n"
        f"👉 *`{otp_code}`*\n\n"
        f"Hãy nhập mã này vào trang đăng nhập OpenAI để hoàn tất.",
        reply_markup=chatgpt_accounts_keyboard([account], show_back_to_list=True),
        parse_mode="Markdown",
    )



# ─── Main menu / back to menu ────────────────────────────────────────────────

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    customer = await _find_customer_by_chat_id(chat_id)

    if customer:
        enrollments = await sync_to_async(list)(customer.enrollments.select_related("course").all())
        course_count = len(enrollments)
        role_line = "\n👑 Vai trò: **ADMIN**" if _is_admin_customer(customer) else ""
        await query.edit_message_text(
            f"🎓 *Xin chào {escape_markdown(customer.full_name) or 'bạn'}!*{role_line}\n\n"
            f"📧 `{customer.customer_email}`\n"
            f"📚 *{course_count}* khóa học đang theo dõi\n\n"
            f"Tôi có thể giúp gì cho bạn hôm nay? 👇",
            reply_markup=_menu_for_customer(customer),
            parse_mode="Markdown",
        )
    else:
        await query.edit_message_text(
            "👋 Bạn chưa liên kết tài khoản.\n\nGõ /start để bắt đầu.",
            reply_markup=restart_keyboard(),
        )


# ─── Courses page callback ───────────────────────────────────────────────────

async def courses_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    page = int(query.data.split("_")[2])

    chat_id = update.effective_chat.id
    customer = await _find_customer_by_chat_id(chat_id)
    if not customer:
        await query.edit_message_text("Bạn chưa liên kết tài khoản.", reply_markup=restart_keyboard())
        return

    enrollments = await sync_to_async(list)(customer.enrollments.select_related("course").all())
    course_data = [(e.course.name, e.course_id) for e in enrollments]

    await query.edit_message_text(
        "📚 *Khóa học của bạn:*\nChọn khóa học để xem chi tiết.",
        reply_markup=course_list_keyboard(course_data, page),
        parse_mode="Markdown",
    )


# ─── Restart flow ────────────────────────────────────────────────────────────

async def restart_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    try:
        await query.edit_message_text(
            "👋 *Xin chào!*\n\nVui lòng nhập *email* của bạn để bắt đầu.",
            reply_markup=restart_keyboard(),
            parse_mode="Markdown",
        )
    except Exception as e:
        if "Message is not modified" not in str(e):
            logger.warning(f"Lỗi edit_message_text trong restart_flow: {e}")
    return ASK_EMAIL


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Đã hủy. Gõ /start để bắt đầu lại.",
        reply_markup=restart_keyboard(),
    )
    return ConversationHandler.END


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def _find_customer_by_chat_id(chat_id: int):
    from .models import Customer
    return await sync_to_async(Customer.objects.filter(telegram_chat_id=chat_id, is_verified_telegram=True).first)()


async def _reply_not_linked(update: Update) -> None:
    text = "❌ Bạn chưa liên kết tài khoản Telegram.\n\nGõ /start và nhập email để liên kết."
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=restart_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=restart_keyboard())


async def unlink_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    chat_id = update.effective_chat.id

    from .models import Customer
    customer = await sync_to_async(Customer.objects.filter(telegram_chat_id=chat_id).first)()

    if customer:
        email = customer.customer_email
        customer.telegram_chat_id = None
        customer.is_verified_telegram = False
        customer.telegram_otp = None
        customer.telegram_otp_created_at = None
        await sync_to_async(customer.save)()

        await update.message.reply_text(
            f"🔗 *Đã huỷ liên kết tài khoản thành công!*\n\n"
            f"Tài khoản Telegram của bạn đã ngắt kết nối với email `{email}`.\n"
            f"Vui lòng nhập *email* mới của bạn để bắt đầu liên kết.",
            reply_markup=restart_keyboard(),
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "👋 *Xin chào!*\n\nVui lòng nhập *email* của bạn để bắt đầu.",
            reply_markup=restart_keyboard(),
            parse_mode="Markdown",
        )

    return ASK_EMAIL


async def unlink_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    chat_id = update.effective_chat.id

    from .models import Customer
    customer = await sync_to_async(Customer.objects.filter(telegram_chat_id=chat_id).first)()

    if customer:
        email = customer.customer_email
        customer.telegram_chat_id = None
        customer.is_verified_telegram = False
        customer.telegram_otp = None
        customer.telegram_otp_created_at = None
        await sync_to_async(customer.save)()

        text = (
            f"🚪 *Đã đăng xuất & Hủy liên kết thành công!*\n\n"
            f"Tài khoản Telegram của bạn đã ngắt kết nối với email `{email}`.\n"
            f"Vui lòng nhấn nút bên dưới hoặc gõ lệnh /start để bắt đầu liên kết mới."
        )
    else:
        text = (
            "👋 *Xin chào!*\n\nVui lòng nhấn nút bên dưới hoặc gõ lệnh /start để bắt đầu."
        )

    await query.edit_message_text(
        text,
        reply_markup=restart_keyboard(),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


# ─── Build application ──────────────────────────────────────────────────────

def build_application() -> Application:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN chưa được cấu hình trong .env")

    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("unlink", unlink_command),
            CallbackQueryHandler(restart_flow, pattern="^restart_flow$"),
        ],
        states={
            ASK_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email),
                CallbackQueryHandler(restart_flow, pattern="^restart_flow$"),
            ],
            ASK_OTP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_otp),
                CallbackQueryHandler(restart_flow, pattern="^restart_flow$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
            CommandHandler("unlink", unlink_command),
        ],
        per_chat=True,
        per_user=True,
        per_message=False,
    )

    admin_add_conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler("adduser", admin_add_user_prompt),
            CallbackQueryHandler(admin_add_user_prompt, pattern="^admin_add_user$"),
        ],
        states={
            ASK_ADMIN_NEW_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_add_email),
                CallbackQueryHandler(restart_flow, pattern="^restart_flow$"),
            ],
            ASK_ADMIN_NEW_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_add_name),
                CallbackQueryHandler(restart_flow, pattern="^restart_flow$"),
            ],
            ASK_ADMIN_NEW_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_add_phone),
                CallbackQueryHandler(restart_flow, pattern="^restart_flow$"),
            ],
            ASK_ADMIN_COURSES: [
                CallbackQueryHandler(admin_course_toggle, pattern=r"^admin_course_toggle_\d+$"),
                CallbackQueryHandler(admin_course_page_change, pattern=r"^admin_course_page_\d+$"),
                CallbackQueryHandler(admin_course_confirm, pattern="^admin_course_confirm$"),
                CallbackQueryHandler(admin_course_cancel, pattern="^admin_course_cancel$"),
                CallbackQueryHandler(restart_flow, pattern="^restart_flow$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
        per_chat=True,
        per_user=True,
        per_message=False,
    )

    application.add_handler(conversation_handler)
    application.add_handler(admin_add_conversation_handler)
    application.add_handler(CommandHandler("accounts", accounts_command))
    application.add_handler(CallbackQueryHandler(accounts_callback, pattern="^view_accounts$"))
    application.add_handler(CommandHandler("me", my_info))
    application.add_handler(CommandHandler("courses", my_courses))
    application.add_handler(CommandHandler("lookup", lookup_customer))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("otp", otp_command))
    application.add_handler(CommandHandler("unlink", unlink_command))
    application.add_handler(CallbackQueryHandler(unlink_callback, pattern="^unlink_account$"))
    application.add_handler(CallbackQueryHandler(restart_flow, pattern="^restart_flow$"))
    application.add_handler(CallbackQueryHandler(fetch_openai_otp, pattern="^fetch_openai_otp$"))
    application.add_handler(CallbackQueryHandler(fetch_chatgpt_otp, pattern="^get_chatgpt_otp_\\d+$"))
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(my_info, pattern="^my_info$"))
    application.add_handler(CallbackQueryHandler(my_courses, pattern="^my_courses$"))
    application.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(course_detail, pattern="^course_\\d+$"))
    application.add_handler(CallbackQueryHandler(courses_page_callback, pattern="^courses_page_\\d+$"))
    application.add_handler(CallbackQueryHandler(lambda u, c: None, pattern="^noop$"))

    return application


def run_bot() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    app = build_application()
    print("Bot dang chay va lang nghe tin nhan...")
    app.run_polling()
