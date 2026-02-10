@echo off
echo ==========================================
echo 🐞 Debug Mode: Brain Tumor Analysis System
echo ==========================================
echo.

echo 1. Checking Python Environment...
python --version 2>NUL
if %errorlevel% neq 0 (
    echo ❌ Python not found in PATH!
    echo    Please install Python (python.org) and add it to your PATH.
    echo    Or if you have it installed, check your environment variables.
    pause
    exit /b
)
echo ✅ Python found.

cd backend
if not exist venv (
    echo    Creating virtual environment...
    python -m venv venv
)

echo    Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ Failed to activate virtual environment.
    pause
    exit /b
)

echo    Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install Python dependencies.
    pause
    exit /b
)

echo    Starting Backend Server (in new window)...
start "Backend API Debug" cmd /k "python -m uvicorn main:app --reload --port 8000"

cd ..
echo.

echo 2. Checking Node.js Environment...
cd frontend
call npm --version 2>NUL
if %errorlevel% neq 0 (
    echo ❌ Node.js/npm not found in PATH!
    echo    Please install Node.js (nodejs.org) to run the frontend.
    pause
    exit /b
)
echo ✅ Node.js found.

if not exist node_modules (
    echo    Installing frontend dependencies...
    call npm install
    if %errorlevel% neq 0 (
        echo ❌ Failed to install Node modules.
        pause
        exit /b
    )
)

echo 3. Starting Frontend Server...
echo    This window will now show frontend logs.
echo    When you see "Ready", open http://localhost:3000
echo.
npm run dev

pause
