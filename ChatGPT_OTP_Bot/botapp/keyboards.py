from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


def build_start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["/start"]],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Bấm /start để bắt đầu",
    )


def build_restart_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Bắt đầu lại", callback_data="restart_flow")]]
    )


def build_fetch_otp_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Lấy OTP từ Gmail OpenAI", callback_data="fetch_openai_otp")]]
    )
