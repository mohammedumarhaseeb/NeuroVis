@echo off
echo ========================================
echo 🚀 Brain Tumor MRI Analysis System
echo ========================================
echo.

echo 1️⃣  Starting Backend...
cd backend
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo [INFO] Installing requirements...
pip install -r requirements.txt
start "Backend API" cmd /k "title Backend API && python main.py"
echo    ✓ Backend started on port 8000
cd ..

echo.
echo 2️⃣  Starting Frontend...
cd frontend
echo [INFO] Installing frontend dependencies...
call npm install
start "Frontend UI" cmd /k "title Frontend UI && npm run dev"
echo    ✓ Frontend started on port 3000
cd ..

echo.
echo ========================================
echo ✅ System is launching!
echo.
echo    Backend API:  http://localhost:8000/docs
echo    Frontend UI:  http://localhost:3000
echo.
echo    Opening browser in 10 seconds...
echo ========================================

timeout /t 10 >nul
start http://localhost:3000
