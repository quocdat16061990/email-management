#!/bin/bash

# Hủy tất cả các tiến trình con khi nhấn Ctrl+C
cleanup() {
    echo ""
    echo "=========================================="
    echo " Đang dừng tất cả các dịch vụ..."
    echo "=========================================="
    kill $FRONTEND_PID $BACKEND_PID $BOT_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "=========================================="
echo " KHỞI CHẠY HỆ THỐNG ANHLAPTRINH MANAGEMENT"
echo "=========================================="
echo ""

# 0. Cài đặt các thư viện nếu còn thiếu
echo "-> Đang kiểm tra và cài đặt thư viện Python (Backend)..."
pip install -r requirements.txt
echo "-> Đang kiểm tra và cài đặt thư viện NPM (Frontend)..."
cd frontend && npm install && cd ..
echo ""

# 1. Khởi chạy Frontend
echo "[1/3] Đang khởi chạy Frontend (Vite)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
sleep 2 # Đợi 2 giây cho frontend khởi động

# 2. Khởi chạy Backend Django
echo "[2/3] Đang khởi chạy Backend (Django Server)..."
python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!
sleep 2 # Đợi 2 giây cho backend khởi động

# 3. Khởi chạy Telegram Bot
echo "[3/3] Đang khởi chạy Telegram Bot..."
python otp_bot.py &
BOT_PID=$!

echo ""
echo "=========================================="
echo " ĐÃ BẬT THÀNH CÔNG TẤT CẢ DỊCH VỤ!"
echo " - Link Web: http://localhost:5173"
echo " - Nhấn Ctrl+C để dừng tất cả dịch vụ cùng lúc."
echo "=========================================="
echo ""

# Giữ script chạy để theo dõi log
wait
