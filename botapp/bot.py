import logging
import random
import time
from datetime import timedelta

from asgiref.sync import sync_to_async
from django.conf import settings
from django.utils import timezone
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

from .keyboards import chatgpt_accounts_keyboard, main_menu_keyboard, restart_keyboard
from .services import extract_otp_from_account_email, get_or_create_customer_for_otp, is_valid_email, send_telegram_otp_email


logger = logging.getLogger(__name__)

ASK_EMAIL = 0
ASK_OTP = 1
EXPIRED_MESSAGE = "❌ Tài khoản của bạn đã hết hạn sử dụng (giới hạn tối đa 1 năm). Bạn đã bị tự động đăng xuất."


def escape_markdown(text: str) -> str:
    if not text:
        return ""
    for char in ["_", "*", "`", "["]:
        text = text.replace(char, f"\\{char}")
    return text


def _is_admin_customer(customer) -> bool:
    admin_email = (getattr(settings, "EMAIL_ADMIN", "") or "").strip().lower()
    return bool(customer and admin_email and (customer.customer_email or "").strip().lower() == admin_email)


def _is_staff_customer(customer) -> bool:
    return bool(customer and (customer.is_staff or _is_admin_customer(customer)))


async def _find_customer_by_chat_id(chat_id: int):
    from .models import Customer

    return await sync_to_async(Customer.objects.filter(telegram_chat_id=chat_id, is_verified_telegram=True).first)()


async def _expire_customer_if_needed(customer) -> bool:
    if not customer or not customer.expiry_date:
        return False
    if timezone.localdate() <= customer.expiry_date:
        return False
    customer.telegram_chat_id = None
    customer.is_verified_telegram = False
    customer.status = "EXPIRED"
    customer.telegram_otp = None
    customer.telegram_otp_created_at = None
    await sync_to_async(customer.save)(
        update_fields=["telegram_chat_id", "is_verified_telegram", "status", "telegram_otp", "telegram_otp_created_at"]
    )
    return True


async def _require_active_customer(update: Update):
    customer = await _find_customer_by_chat_id(update.effective_chat.id)
    if not customer:
        await _reply_not_linked(update)
        return None
    if await _expire_customer_if_needed(customer):
        if update.callback_query:
            await update.callback_query.edit_message_text(EXPIRED_MESSAGE, reply_markup=restart_keyboard())
        else:
            await update.message.reply_text(EXPIRED_MESSAGE, reply_markup=restart_keyboard())
        return None
    return customer


def _menu_for_customer(customer):
    return main_menu_keyboard(is_admin=_is_staff_customer(customer))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    customer = await _find_customer_by_chat_id(update.effective_chat.id)
    if customer and await _expire_customer_if_needed(customer):
        await update.message.reply_text(EXPIRED_MESSAGE, reply_markup=restart_keyboard())
        return ConversationHandler.END
    if customer:
        role_line = "\n👑 Vai trò: ADMIN/STAFF" if _is_staff_customer(customer) else ""
        await update.message.reply_text(
            f"Xin chào {escape_markdown(customer.full_name) or 'bạn'}!{role_line}\n\n"
            f"Email: `{customer.customer_email}`\n"
            f"Hạn sử dụng: `{customer.expiry_date or 'N/A'}`\n\n"
            "Chọn chức năng bên dưới.",
            reply_markup=_menu_for_customer(customer),
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Chào mừng bạn đến với hệ thống lấy OTP ChatGPT.\n\n"
        "Vui lòng nhập email của bạn để liên kết Telegram.\n"
        "Nếu email chưa tồn tại, hệ thống sẽ tự động tạo tài khoản với hạn sử dụng 1 năm.",
        reply_markup=restart_keyboard(),
    )
    return ASK_EMAIL


async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email_text = update.message.text.strip().lower()
    if not is_valid_email(email_text):
        await update.message.reply_text("❌ Email không hợp lệ. Vui lòng nhập lại.", reply_markup=restart_keyboard())
        return ASK_EMAIL

    from .models import Customer

    customer = await sync_to_async(Customer.objects.filter(customer_email=email_text).first)()
    if customer and customer.is_verified_telegram:
        await update.message.reply_text(
            "❌ Email này đã được liên kết với một tài khoản Telegram.",
            reply_markup=restart_keyboard(),
        )
        return ConversationHandler.END

    otp_code = f"{random.randint(100000, 999999)}"
    try:
        await sync_to_async(get_or_create_customer_for_otp)(email_text, otp_code)
        email_sent = await sync_to_async(send_telegram_otp_email)(email_text, otp_code)
        if not email_sent:
            raise RuntimeError("Không gửi được OTP xác thực Telegram.")
    except Exception:
        logger.exception("Không tạo được phiên xác thực Telegram.")
        await update.message.reply_text("❌ Không gửi được mã xác thực. Vui lòng thử lại sau.", reply_markup=restart_keyboard())
        return ConversationHandler.END

    context.user_data["pending_email"] = email_text
    context.user_data["otp_attempts"] = 0
    await update.message.reply_text(
        f"🔑 Đã gửi mã OTP 6 số đến `{email_text}`. Mã có hiệu lực trong 10 phút.",
        reply_markup=restart_keyboard(),
        parse_mode="Markdown",
    )
    return ASK_OTP


async def handle_otp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    otp_text = update.message.text.strip()
    email_text = context.user_data.get("pending_email")
    chat_id = update.effective_chat.id
    if not email_text:
        await update.message.reply_text("❌ Phiên xác thực không hợp lệ. Vui lòng bấm /start.", reply_markup=restart_keyboard())
        return ConversationHandler.END

    from .models import Customer

    customer = await sync_to_async(Customer.objects.filter(customer_email=email_text).first)()
    if not customer:
        await update.message.reply_text("❌ Không tìm thấy khách hàng. Vui lòng bấm /start.", reply_markup=restart_keyboard())
        return ConversationHandler.END

    now = timezone.now()
    otp_expired = customer.telegram_otp_created_at and now > customer.telegram_otp_created_at + timedelta(minutes=10)
    if otp_expired or not customer.telegram_otp or customer.telegram_otp != otp_text:
        attempts = context.user_data.get("otp_attempts", 0) + 1
        context.user_data["otp_attempts"] = attempts
        if attempts >= 5:
            context.user_data.clear()
            await update.message.reply_text("❌ Bạn đã nhập sai OTP quá nhiều lần. Vui lòng bấm /start.", reply_markup=restart_keyboard())
            return ConversationHandler.END
        await update.message.reply_text(f"❌ OTP không đúng hoặc đã hết hạn ({attempts}/5).", reply_markup=restart_keyboard())
        return ASK_OTP

    today = timezone.localdate()
    await sync_to_async(
        lambda: Customer.objects.filter(telegram_chat_id=chat_id)
        .exclude(customer_email=email_text)
        .update(telegram_chat_id=None, is_verified_telegram=False)
    )()
    customer.telegram_chat_id = chat_id
    customer.is_verified_telegram = True
    customer.telegram_otp = None
    customer.telegram_otp_created_at = None
    customer.registration_date = customer.registration_date or today
    customer.expiry_date = customer.expiry_date or (today + timedelta(days=365))
    customer.status = "ACTIVE"
    await sync_to_async(customer.save)()

    context.user_data.clear()
    await update.message.reply_text(
        f"✅ Xác thực thành công!\n\nEmail: `{email_text}`\nHạn sử dụng: `{customer.expiry_date}`",
        reply_markup=_menu_for_customer(customer),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def my_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    customer = await _require_active_customer(update)
    if not customer:
        return
    text = (
        "👤 Thông tin của bạn\n\n"
        f"Email: `{customer.customer_email}`\n"
        f"Họ tên: {escape_markdown(customer.full_name) or 'Chưa cập nhật'}\n"
        f"SĐT: {customer.phone_number or 'Chưa cập nhật'}\n"
        f"Trạng thái: {customer.status}\n"
        f"Hạn sử dụng: `{customer.expiry_date or 'N/A'}`"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=_menu_for_customer(customer), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=_menu_for_customer(customer), parse_mode="Markdown")


async def show_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None) -> None:
    customer = await _require_active_customer(update)
    if not customer:
        return

    from .models import ChatGPTAccount

    qs = ChatGPTAccount.objects.filter(status="ACTIVE").order_by("email")
    if _is_staff_customer(customer):
        accounts = await sync_to_async(list)(qs)
    else:
        accounts = await sync_to_async(list)(customer.allowed_chatgpt_accounts.filter(status="ACTIVE").order_by("email"))
    if not accounts:
        msg = "❌ Tài khoản Telegram của bạn chưa được cấp email ChatGPT nào để lấy OTP."
        if query:
            await query.edit_message_text(msg, reply_markup=_menu_for_customer(customer))
        else:
            await update.message.reply_text(msg, reply_markup=_menu_for_customer(customer))
        return

    message_text = "📋 Chọn tài khoản ChatGPT cần lấy OTP sau khi bạn đã yêu cầu gửi mã từ OpenAI."
    reply_markup = chatgpt_accounts_keyboard(accounts)
    if query:
        await query.edit_message_text(message_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message_text, reply_markup=reply_markup)


async def accounts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await show_accounts(update, context, query=query)


async def fetch_chatgpt_otp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    customer = await _require_active_customer(update)
    if not customer:
        return

    account_id = int(query.data.split("_")[3])
    from .models import ChatGPTAccount

    qs = ChatGPTAccount.objects.filter(id=account_id, status="ACTIVE")
    if not _is_staff_customer(customer):
        custom_account_ids = await sync_to_async(list)(customer.allowed_chatgpt_accounts.values_list("id", flat=True))
        qs = qs.filter(id__in=custom_account_ids)
    account = await sync_to_async(qs.first)()
    if not account:
        await query.edit_message_text("❌ Bạn không có quyền truy cập tài khoản ChatGPT này.", reply_markup=_menu_for_customer(customer))
        return

    await query.edit_message_text(f"🔍 Đang quét Gmail của `{account.email}` để tìm OTP OpenAI...", parse_mode="Markdown")
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
            f"❌ Không đọc được Gmail của `{account.email}` lúc này.",
            reply_markup=chatgpt_accounts_keyboard([account], show_back_to_list=True),
            parse_mode="Markdown",
        )
        return

    if not otp_code:
        await query.edit_message_text(
            f"⏳ Không tìm thấy OTP OpenAI cho `{account.email}` trong 2 phút.",
            reply_markup=chatgpt_accounts_keyboard([account], show_back_to_list=True),
            parse_mode="Markdown",
        )
        return

    await query.edit_message_text(
        f"🔑 Mã OTP của `{account.email}` là:\n\n👉 *`{otp_code}`*",
        reply_markup=chatgpt_accounts_keyboard([account], show_back_to_list=True),
        parse_mode="Markdown",
    )


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    customer = await _require_active_customer(update)
    if not customer:
        return
    await query.edit_message_text(
        f"Xin chào {escape_markdown(customer.full_name) or 'bạn'}!\n\nEmail: `{customer.customer_email}`",
        reply_markup=_menu_for_customer(customer),
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Lệnh hỗ trợ:\n"
        "/start - liên kết tài khoản Telegram\n"
        "/me - xem thông tin tài khoản\n"
        "/accounts - lấy danh sách tài khoản ChatGPT có thể lấy OTP\n"
        "/unlink - đăng xuất Telegram"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=restart_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=restart_keyboard())


async def accounts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_accounts(update, context)


async def restart_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("Vui lòng nhập email của bạn để liên kết Telegram.", reply_markup=restart_keyboard())
    return ASK_EMAIL


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Đã hủy. Gõ /start để bắt đầu lại.", reply_markup=restart_keyboard())
    return ConversationHandler.END


async def _reply_not_linked(update: Update) -> None:
    text = "❌ Bạn chưa liên kết tài khoản Telegram.\n\nGõ /start và nhập email để liên kết."
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=restart_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=restart_keyboard())


async def unlink_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    chat_id = update.effective_chat.id

    from .models import Customer

    customer = await sync_to_async(Customer.objects.filter(telegram_chat_id=chat_id).first)()
    if customer:
        customer.telegram_chat_id = None
        customer.is_verified_telegram = False
        customer.telegram_otp = None
        customer.telegram_otp_created_at = None
        await sync_to_async(customer.save)()
    await update.message.reply_text("Đã đăng xuất Telegram. Vui lòng nhập email để liên kết lại.", reply_markup=restart_keyboard())
    return ASK_EMAIL


async def unlink_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    chat_id = update.effective_chat.id

    from .models import Customer

    customer = await sync_to_async(Customer.objects.filter(telegram_chat_id=chat_id).first)()
    if customer:
        customer.telegram_chat_id = None
        customer.is_verified_telegram = False
        customer.telegram_otp = None
        customer.telegram_otp_created_at = None
        await sync_to_async(customer.save)()
    await query.edit_message_text("Đã đăng xuất Telegram. Bấm /start để liên kết lại.", reply_markup=restart_keyboard())
    return ConversationHandler.END


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
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start), CommandHandler("unlink", unlink_command)],
        per_chat=True,
        per_user=True,
        per_message=False,
    )
    application.add_handler(conversation_handler)
    application.add_handler(CommandHandler("accounts", accounts_command))
    application.add_handler(CommandHandler("me", my_info))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("unlink", unlink_command))
    application.add_handler(CallbackQueryHandler(accounts_callback, pattern="^view_accounts$"))
    application.add_handler(CallbackQueryHandler(fetch_chatgpt_otp, pattern="^get_chatgpt_otp_\\d+$"))
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(my_info, pattern="^my_info$"))
    application.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(unlink_callback, pattern="^unlink_account$"))
    application.add_handler(CallbackQueryHandler(restart_flow, pattern="^restart_flow$"))
    return application


def run_bot() -> None:
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    app = build_application()
    print("Bot đang chạy và lắng nghe tin nhắn...")
    app.run_polling()
