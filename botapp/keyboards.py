from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("👤 Thông tin của tôi", callback_data="my_info")],
        [InlineKeyboardButton("🔑 Lấy OTP ChatGPT", callback_data="view_accounts")],
        [InlineKeyboardButton("❓ Trợ giúp", callback_data="help")],
        [InlineKeyboardButton("🚪 Đăng xuất", callback_data="unlink_account")],
    ]
    return InlineKeyboardMarkup(buttons)


def restart_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Bắt đầu lại", callback_data="restart_flow")],
    ])


def chatgpt_accounts_keyboard(accounts: list, show_back_to_list: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    for account in accounts:
        buttons.append([
            InlineKeyboardButton(
                f"🔑 Lấy OTP: {account.email}",
                callback_data=f"get_chatgpt_otp_{account.id}",
            )
        ])
    if show_back_to_list:
        buttons.append([InlineKeyboardButton("🔙 Quay lại danh sách", callback_data="view_accounts")])
    buttons.append([InlineKeyboardButton("🔙 Quay lại menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)
