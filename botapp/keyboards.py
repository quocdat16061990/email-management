from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    otp_button_text = "🔑 Lấy danh sách Email OTP ChatGPT" if is_admin else "🔑 Lấy mã OTP OpenAI"
    buttons = [
        [InlineKeyboardButton("👤 Thông tin của tôi", callback_data="my_info")],
        [InlineKeyboardButton("📚 Khóa học của tôi", callback_data="my_courses")],
        [InlineKeyboardButton(otp_button_text, callback_data="fetch_openai_otp")],
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton("➕ Thêm người mới", callback_data="admin_add_user")])
    buttons.extend([
        [InlineKeyboardButton("❓ Trợ giúp", callback_data="help")],
        [InlineKeyboardButton("🚪 Đăng xuất", callback_data="unlink_account")],
    ])
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
        [InlineKeyboardButton("🔑 Lấy mã OTP OpenAI", callback_data="fetch_openai_otp")],
        [InlineKeyboardButton("🔙 Quay lại", callback_data="main_menu")],
    ])


def admin_course_selection_keyboard(courses: list, selected_ids: set[int] | list[int], page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    selected = set(selected_ids)
    start = page * per_page
    end = start + per_page
    page_courses = courses[start:end]
    total_pages = max(1, (len(courses) + per_page - 1) // per_page)

    buttons = []
    for course in page_courses:
        marker = "✅" if course.id in selected else "⬜"
        buttons.append([
            InlineKeyboardButton(
                f"{marker} {course.name}",
                callback_data=f"admin_course_toggle_{course.id}",
            )
        ])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ Trước", callback_data=f"admin_course_page_{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
    if end < len(courses):
        nav_row.append(InlineKeyboardButton("Sau ▶️", callback_data=f"admin_course_page_{page + 1}"))

    if nav_row:
        buttons.append(nav_row)

    buttons.extend([
        [InlineKeyboardButton("💾 Xác nhận", callback_data="admin_course_confirm")],
        [InlineKeyboardButton("🔙 Hủy", callback_data="admin_course_cancel")],
    ])
    return InlineKeyboardMarkup(buttons)


def restart_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Bắt đầu lại", callback_data="restart_flow")],
    ])


def chatgpt_accounts_keyboard(accounts: list, show_back_to_list: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    for acc in accounts:
        buttons.append([
            InlineKeyboardButton(
                f"🔑 Lấy OTP: {acc.email}",
                callback_data=f"get_chatgpt_otp_{acc.id}"
            )
        ])
    if show_back_to_list:
        buttons.append([InlineKeyboardButton("🔙 Quay lại Danh sách", callback_data="view_accounts")])
    buttons.append([InlineKeyboardButton("🔙 Quay lại Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

