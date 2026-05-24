from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode


from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("👤 Thông tin của tôi", callback_data="my_info")],
        [InlineKeyboardButton("📚 Khóa học của tôi", callback_data="my_courses")],
        [InlineKeyboardButton("🔑 Lấy mã OTP", callback_data="fetch_openai_otp")],
        [InlineKeyboardButton("❓ Trợ giúp", callback_data="help")],
        [InlineKeyboardButton("🚪 Đăng xuất", callback_data="unlink_account")],
    ]
    return InlineKeyboardMarkup(buttons)


def course_list_keyboard(courses: list, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    start = page * per_page
    end = start + per_page
    page_courses = courses[start:end]
    total_pages = max(1, (len(courses) + per_page - 1) // per_page)

    buttons = []
    for course_name, course_id in page_courses:
        buttons.append([InlineKeyboardButton(f"📖 {course_name}", callback_data=f"course_{course_id}")])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ Trước", callback_data=f"courses_page_{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
    if end < len(courses):
        nav_row.append(InlineKeyboardButton("Sau ▶️", callback_data=f"courses_page_{page + 1}"))

    if nav_row:
        buttons.append(nav_row)
    buttons.append([InlineKeyboardButton("🔙 Quay lại", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)


def enrollment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 Lấy OTP OpenAI", callback_data="fetch_openai_otp")],
        [InlineKeyboardButton("🔙 Quay lại", callback_data="main_menu")],
    ])


def restart_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Bắt đầu lại", callback_data="restart_flow")],
    ])
