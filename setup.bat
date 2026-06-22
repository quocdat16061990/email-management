@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo    ANHLAPTRINH MANAGEMENT - WINDOWS SETUP
echo ==========================================
echo.

echo [1/5] Kiểm tra yêu cầu...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python chưa cài. Vui lòng cài Python >= 3.10
    exit /b 1
)
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js chưa cài. Vui lòng cài Node.js >= 18
    exit /b 1
)
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm chưa cài.
    exit /b 1
)
echo - Python: OK
echo - Node.js: OK
echo - npm: OK
echo.

echo [2/5] Kiểm tra file .env...
if not exist .env (
    if exist .env.example (
        copy .env.example .env
        echo [INFO] Đã tạo file .env từ .env.example.
        echo [ERROR] Hãy mở file .env và điền đầy đủ thông tin rồi chạy lại setup.bat.
        exit /b 1
    ) else (
        echo [ERROR] Không tìm thấy file .env.example.
        exit /b 1
    )
)

:: Validate .env using python
python -c "import os; data={}; f=open('.env','r',encoding='utf-8'); [data.update({line.split('=',1)[0].strip(): line.split('=',1)[1].strip().strip('\"').strip('\'')}) for line in f if line.strip() and not line.strip().startswith('#') and '=' in line]; keys=['TELEGRAM_BOT_TOKEN','EMAIL_ACCOUNT','APP_PASSWORD','DB_HOST','DB_PORT','DB_NAME','DB_USER','DB_PASSWORD']; missing=[k for k in keys if k not in data or not data[k] or data[k] in ['nhập_token_của_bạn_vào_đây','email_của_bạn@gmail.com','mật_khẩu_app_của_bạn','mật_khẩu_DB_của_bạn','nhap_token_cua_ban_vao_day','email_cua_ban@gmail.com','mat_khau_app_cua_ban','mat_khau_DB_cua_ban']]; print('Missing keys: ' + ', '.join(missing)) if missing else None; exit(1 if missing else 0)"
if %errorlevel% neq 0 (
    echo [ERROR] File .env chưa được cấu hình đầy đủ. Vui lòng kiểm tra lại.
    exit /b 1
)
echo - File .env: OK
echo.

echo [3/5] Cài thư viện Python...
python -m pip install --upgrade pip -q
pip install -r requirements.txt
pip install requests
echo - Thư viện Python: OK
echo.

echo [4/5] Cài thư viện Frontend (Node)...
if exist frontend (
    cd frontend
    call npm install
    cd ..
    echo - Thư viện Node (Frontend): OK
) else (
    echo [WARNING] Không tìm thấy thư mục frontend/
)
echo.

echo [5/5] Migrate database Supabase...
python manage.py migrate --run-syncdb
echo - Database migrated: OK
echo.

echo.

echo ==========================================
echo    CÀI ĐẶT HOÀN TẤT!
echo ==========================================
echo.
echo Chạy ứng dụng bằng 3 terminal riêng biệt:
echo.
echo Terminal 1 - Backend:
echo   python manage.py runserver
echo.
echo Terminal 2 - Frontend:
echo   cd frontend
echo   npm run dev
echo.
echo Terminal 3 - Telegram Bot:
echo   python manage.py run_otp_bot
echo.
echo Link Web: http://localhost:5173/
echo Login: admin@example.com / change-me
echo.
pause
