import logging
import time

from asgiref.sync import sync_to_async
from django.conf import settings
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

from .keyboards import build_fetch_otp_keyboard, build_restart_keyboard, build_start_keyboard
from .services import (
    create_or_update_customer,
    extract_otp_from_openai_email,
    is_valid_email,
    mark_customer_otp_received,
)


logger = logging.getLogger(__name__)

ASK_EMAIL = 0


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Xin chào. Bấm /start để bắt đầu.\n\nVui lòng nhập email của bạn.",
        reply_markup=build_start_keyboard(),
    )
    return ASK_EMAIL


async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email_text = update.message.text.strip()

    if not is_valid_email(email_text):
        await update.message.reply_text("Email không hợp lệ. Vui lòng nhập lại email của bạn.")
        return ASK_EMAIL

    try:
        await sync_to_async(create_or_update_customer)(update.effective_chat.id, email_text)
    except Exception:
        logger.exception("Không tạo được phiên customer.")
        await update.message.reply_text(
            "Không khởi tạo được phiên làm việc lúc này. Vui lòng thử lại sau.",
            reply_markup=build_restart_keyboard(),
        )
        return ConversationHandler.END

    context.user_data["email"] = email_text
    context.user_data["otp_session_started_at"] = time.time()
    await update.message.reply_text(
        "Email hợp lệ.\n"
        "Bây giờ hãy bấm gửi OTP trên trang OpenAI, sau đó bấm nút bên dưới để tôi lấy OTP từ Gmail.",
        reply_markup=build_fetch_otp_keyboard(),
    )
    return ConversationHandler.END


async def fetch_openai_otp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    email_text = context.user_data.get("email")

    if not email_text:
        context.user_data.clear()
        await query.message.reply_text(
            "Phiên xác thực không còn hợp lệ. Vui lòng bấm /start để thử lại.",
            reply_markup=build_start_keyboard(),
        )
        return

    await query.message.reply_text("Đang quét Gmail để tìm OTP OpenAI...")
    try:
        otp_code = await sync_to_async(extract_otp_from_openai_email)(
            timeout_seconds=settings.OTP_TTL_MINUTES * 60,
            interval_seconds=5,
            min_received_timestamp=context.user_data.get("otp_session_started_at"),
        )
    except Exception:
        logger.exception("Không đọc được Gmail OpenAI OTP.")
        await query.message.reply_text(
            "Không đọc được Gmail lúc này. Kiểm tra lại EMAIL_ACCOUNT và APP_PASSWORD.",
            reply_markup=build_restart_keyboard(),
        )
        return

    if not otp_code:
        await query.message.reply_text(
            "Không tìm thấy OTP OpenAI trong vòng 1 phút. Hãy bấm gửi OTP bên OpenAI rồi thử lại.",
            reply_markup=build_fetch_otp_keyboard(),
        )
        return

    await sync_to_async(mark_customer_otp_received)(query.message.chat_id, email_text)
    await query.message.reply_text(
        f"OTP OpenAI của bạn là: {otp_code}\nXong rồi. Cảm ơn bạn.",
        reply_markup=build_restart_keyboard(),
    )
    context.user_data.clear()


async def restart_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.message.reply_text(
        "Xin chào. Bấm /start để bắt đầu.\n\nVui lòng nhập email của bạn.",
        reply_markup=build_start_keyboard(),
    )
    return ASK_EMAIL


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Đã hủy phiên hiện tại. Bấm /start nếu muốn bắt đầu lại.",
        reply_markup=build_start_keyboard(),
    )
    return ConversationHandler.END


def build_application() -> Application:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN chưa được cấu hình trong .env")

    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_chat=True,
        per_user=True,
        per_message=False,
    )
    application.add_handler(conversation_handler)
    application.add_handler(CallbackQueryHandler(restart_flow, pattern="^restart_flow$"))
    application.add_handler(CallbackQueryHandler(fetch_openai_otp, pattern="^fetch_openai_otp$"))
    return application


def run_bot() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    app = build_application()
    print("Bot dang chay va lang nghe tin nhan...")
    app.run_polling()
