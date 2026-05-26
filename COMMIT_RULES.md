# Quy Tắc Commit Message (Commit Rules)

Dự án này sử dụng công cụ tự động **Husky** để kiểm tra và bắt buộc định dạng thông điệp commit (commit message) tuân thủ theo chuẩn **Conventional Commits**. Nếu viết sai định dạng, lệnh commit của bạn sẽ bị hệ thống tự động từ chối.

---

## 1. Cấu trúc chuẩn của Commit Message

Thông điệp commit phải được viết theo cấu trúc sau:

```text
<type>(<scope>): <mô tả ngắn bằng tiếng Việt không dấu hoặc có dấu>
```

* **`<type>`** (Bắt buộc): Loại thay đổi bạn thực hiện (danh sách loại hợp lệ ở phần dưới).
* **`(<scope>)`** (Tùy chọn): Phạm vi ảnh hưởng của thay đổi (ví dụ: `bot`, `web`, `frontend`, `db`).
* **`:`** (Bắt buộc): Dấu hai chấm theo sau là một dấu cách trống.
* **`<mô tả>`** (Bắt buộc): Mô tả ngắn gọn, súc tích về thay đổi bạn đã thực hiện.

---

## 2. Các loại Commit hợp lệ (`<type>`)

Bạn chỉ được phép sử dụng một trong các từ khóa sau cho trường `<type>`:

| Loại (Type) | Ý nghĩa | Ví dụ |
| :--- | :--- | :--- |
| **`feat`** | Thêm tính năng mới (Feature) | `feat: them nut phan trang danh sach khoa hoc` |
| **`fix`** | Sửa lỗi (Bug fix) | `fix(bot): sua loi entity markdown khi ten chua dau gach duoi` |
| **`docs`** | Cập nhật tài liệu hướng dẫn (Documentation) | `docs: cap nhat file huong dan COMMIT_RULES.md` |
| **`style`** | Thay đổi giao diện, định dạng code (không ảnh hưởng logic) | `style: căn chỉnh lề nút bấm trang login` |
| **`refactor`** | Tái cấu trúc lại code (không sửa bug cũng không thêm tính năng) | `refactor: chia nho cac helper function trong bot.py` |
| **`perf`** | Tối ưu hiệu năng (Performance) | `perf: tang toc do quet Gmail OTP` |
| **`test`** | Thêm hoặc sửa mã kiểm thử (Tests) | `test: bo sung unit test cho AuthContext` |
| **`build`** | Thay đổi các file build, dependencies (npm, pip, docker) | `build: nang cap thu vien python-telegram-bot` |
| **`ci`** | Cập nhật cấu hình CI/CD (GitHub Actions, Docker) | `ci: cap nhat file workflows/ci-cd.yml` |
| **`chore`** | Các công việc linh tinh khác không thuộc các mục trên | `chore: xoa file nhuannvn.txt` |
| **`revert`** | Khôi phục lại một commit trước đó | `revert: quay lai commit feat: them nut login` |

---

## 3. Các ví dụ mẫu

### Ví dụ ĐÚNG (Commit thành công):
* `feat: them chuc nang phan trang danh sach khoa hoc`
* `fix(bot): sua loi timeout khi goi API dang ky Voomly`
* `docs: bo sung huong dan luat commit message`
* `chore: don dep cac file rác trong thu muc goc`

### Ví dụ SAI (Commit sẽ bị chặn và từ chối):
* `hello` (Thiếu type và sai định dạng hoàn toàn)
* `them nut add user` (Thiếu type và dấu `:`)
* `testing: viet them unit test` (Loại `testing` không hợp lệ, phải dùng `test`)
* `fix sua loi database` (Thiếu dấu hai chấm `:`)

---

## 4. Cách kiểm tra thủ công

Để kiểm tra xem commit message có hợp lệ hay không trước khi thực hiện commit thực tế, bạn có thể chạy thử lệnh kiểm tra regex:

```bash
# Thay đổi "thông điệp của bạn" và chạy lệnh sau trên terminal:
echo "feat: thong diep cua ban" | grep -Eq "^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?: .+" && echo "Hợp lệ ✅" || echo "Không hợp lệ ❌"
```
