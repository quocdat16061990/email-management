@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo ==========================================
echo  KHOI CHAY HE THONG ANHLAPTRINH MANAGEMENT
echo ==========================================
echo.

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

set "FRONTEND_TITLE=EMAIL_MGMT_FRONTEND"
set "BACKEND_TITLE=EMAIL_MGMT_BACKEND"
set "BOT_TITLE=EMAIL_MGMT_BOT"

echo [1/3] Dang khoi chay Frontend (Vite)...
start "%FRONTEND_TITLE%" cmd /k "cd /d ""%ROOT_DIR%\frontend"" && npm run dev"
timeout /t 2 /nobreak >nul

set "PYTHON_CMD=python"
if exist "%ROOT_DIR%\venv\Scripts\python.exe" (
    set "PYTHON_CMD=%ROOT_DIR%\venv\Scripts\python.exe"
)

echo [2/3] Dang khoi chay Backend (Django Server)...
start "%BACKEND_TITLE%" cmd /k "cd /d ""%ROOT_DIR%"" && "!PYTHON_CMD!" manage.py runserver"
timeout /t 2 /nobreak >nul

echo [3/3] Dang khoi chay Telegram Bot...
start "%BOT_TITLE%" cmd /k "cd /d ""%ROOT_DIR%"" && "!PYTHON_CMD!" otp_bot.py"

echo.
echo ==========================================
echo  DA BAT THANH CONG TAT CA DICH VU!
echo  - Link Web: http://localhost:5173
echo  - Dong cua so nay de dung tat ca dich vu cung luc.
echo ==========================================
echo.
echo Nhan phim bat ky de dung tat ca dich vu...
pause >nul

echo.
echo ==========================================
echo  Dang dung tat ca cac dich vu...
echo ==========================================

for %%T in ("%FRONTEND_TITLE%" "%BACKEND_TITLE%" "%BOT_TITLE%") do (
    taskkill /FI "WINDOWTITLE eq %%~T" /T /F >nul 2>&1
)

endlocal
