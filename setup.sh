#!/bin/bash
set -e

# ──────────────────────────────────────────────────
# Anhlaptrinh Management — Setup & Sync Script
# Chạy: chmod +x setup.sh && ./setup.sh
# ──────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[$(date '+%H:%M:%S')]${NC} $1"; }
ok()   { echo -e "  ${GREEN}✅ $1${NC}"; }
warn() { echo -e "  ${YELLOW}⚠️  $1${NC}"; }
fail() { echo -e "  ${RED}❌ $1${NC}"; exit 1; }

# ─── Config ───────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo ""
echo -e "${CYAN}══════════════════════════════════════════${NC}"
echo -e "${CYAN}   ANHLAPTRINH MANAGEMENT — SETUP${NC}"
echo -e "${CYAN}══════════════════════════════════════════${NC}"
echo ""

# ─── Step 1: Check Requirements ───────────────────
log "${YELLOW}[1/6] Kiểm tra yêu cầu...${NC}"

command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1 || fail "Python chưa cài. Cài Python >= 3.10"
PYTHON=$(command -v python3 || command -v python)
ok "Python: $($PYTHON --version 2>&1)"

command -v node >/dev/null 2>&1 || fail "Node.js chưa cài. Cài Node >= 18"
ok "Node.js: $(node --version)"

command -v npm >/dev/null 2>&1 || fail "npm chưa cài"
ok "npm: $(npm --version)"

# ─── Step 2: Check .env ────────────────────────────
log "${YELLOW}[2/6] Kiểm tra file .env...${NC}"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        fail "Chưa có .env. Đã tạo từ .env.example. HÃY MỞ .env VÀ ĐIỀN THÔNG TIN RỒI CHẠY LẠI."
    else
        fail "Không tìm thấy .env.example"
    fi
fi

# Validate required fields
check_env() {
    local key=$1
    local val=$(grep "^${key}=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'" | xargs)
    if [ -z "$val" ] || [ "$val" = "nhập_token_của_bạn_vào_đây" ] || [ "$val" = "email_của_bạn@gmail.com" ] || [ "$val" = "mật_khẩu_app_của_bạn" ] || [ "$val" = "mật_khẩu_DB_của_bạn" ] || [ "$val" = "nhập_token_Voomly_của_bạn" ]; then
        fail "Thiếu: $key trong .env — điền đầy đủ rồi chạy lại."
    fi
}

check_env "TELEGRAM_BOT_TOKEN"
check_env "EMAIL_ACCOUNT"
check_env "APP_PASSWORD"
check_env "DB_HOST"
check_env "DB_PORT"
check_env "DB_NAME"
check_env "DB_USER"
check_env "DB_PASSWORD"
ok ".env đã điền đầy đủ thông tin"

# ─── Step 3: Install Python ────────────────────────
log "${YELLOW}[3/6] Cài thư viện Python...${NC}"

if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
else
    PYTHON=python
fi

# Create venv if not exists
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
    ok "Đã tạo môi trường ảo"
fi

source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null || fail "Không activate được venv"

pip install -q -r requirements.txt 2>&1 | tail -1
ok "Python packages: $(pip list 2>/dev/null | wc -l) packages"

# ─── Step 4: Install Frontend ──────────────────────
log "${YELLOW}[4/6] Cài thư viện Frontend (Node)...${NC}"

if [ -d "frontend" ]; then
    cd frontend
    npm install --silent 2>&1 | tail -1
    cd "$PROJECT_DIR"
    ok "Node packages installed"
else
    warn "Không tìm thấy thư mục frontend/"
fi

# ─── Step 5: Migrate Database ──────────────────────
log "${YELLOW}[5/6] Migrate database Supabase...${NC}"

source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

$PYTHON manage.py migrate --run-syncdb 2>&1
ok "Database migrated"

$PYTHON manage.py showmigrations 2>&1 | grep -c "\[X\]" > /dev/null && ok "Tất cả migrations đã applied"

# ─── Step 6: Sync Voomly ───────────────────────────
log "${YELLOW}[6/6] Đồng bộ dữ liệu từ Voomly...${NC}"

source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

$PYTHON -c "
import os, django, time
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from botapp.services import sync_courses_from_voomly, sync_all_students_from_voomly
from botapp.models import Course, Customer

print('  📚 Đồng bộ khóa học...', end=' ')
t1 = time.time()
r1 = sync_courses_from_voomly()
print(f'{time.time()-t1:.1f}s — tạo mới: {r1[\"created\"]}, cập nhật: {r1[\"updated\"]}, tổng: {r1[\"total\"]}')

print('  👥 Đồng bộ học viên...', end=' ')
t2 = time.time()
r2 = sync_all_students_from_voomly()
print(f'{time.time()-t2:.1f}s — {r2[\"total_students\"]} học viên, {r2[\"courses_count\"]} khóa học')

print(f'  📊 Tổng: {Course.objects.count()} khóa học, {Customer.objects.count()} học viên')
" 2>&1
ok "Đồng bộ Voomly hoàn tất"

# ─── Done ───────────────────────────────────────────
echo ""
echo -e "${GREEN}══════════════════════════════════════════${NC}"
echo -e "${GREEN}   ✅ CÀI ĐẶT HOÀN TẤT!${NC}"
echo -e "${GREEN}══════════════════════════════════════════${NC}"
echo ""
echo -e "  ${CYAN}Chạy ứng dụng:${NC}"
echo ""
echo -e "  ${YELLOW}Terminal 1 — Backend:${NC}"
echo "    cd $PROJECT_DIR"
echo "    source venv/bin/activate"
echo "    python manage.py runserver"
echo ""
echo -e "  ${YELLOW}Terminal 2 — Frontend:${NC}"
echo "    cd $PROJECT_DIR/frontend"
echo "    npm run dev"
echo ""
echo -e "  ${YELLOW}Terminal 3 — Telegram Bot:${NC}"
echo "    cd $PROJECT_DIR"
echo "    source venv/bin/activate"
echo "    python manage.py run_otp_bot"
echo ""
echo -e "  ${CYAN}Web:${NC} http://localhost:5173/"
echo -e "  ${CYAN}Login:${NC} admin@example.com / change-me"
echo ""
