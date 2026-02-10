@echo off
SETLOCAL EnableDelayedExpansion
echo ========================================
echo 🚀 Brain Tumor MRI Analysis System
echo ========================================
echo.

echo 🔧 Repairing Environment Paths...
set "PATH=C:\Windows\System32;C:\Program Files\nodejs;C:\Program Files (x86)\nodejs;%PATH%"

echo 🔍 Detecting Environment...

REM --- 1. FIND PYTHON ---
set PYTHON_CMD=python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    if exist "C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe" (
        set PYTHON_CMD="C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe"
        echo    ✅ Found Python at: !PYTHON_CMD!
    ) else (
        echo    ❌ Python NOT FOUND in PATH or standard locations.
        echo    Please install Python from python.org and add to PATH.
        pause
        exit /b
    )
) else (
    echo    ✅ Python found in PATH.
)

REM --- 2. FIND NODE.JS ---
call npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    ❌ Node.js/npm NOT FOUND!
    echo    The website cannot run without Node.js.
    echo.
    echo    Opening download page...
    start https://nodejs.org
    echo    Please install Node.js (LTS version) and restart this script.
    pause
    exit /b
)
echo    ✅ Node.js found.

echo.
echo 1️⃣ Setup & Start Backend...
cd backend

if not exist venv (
    echo    Creating virtual environment using !PYTHON_CMD!...
    !PYTHON_CMD! -m venv venv
    call venv\Scripts\activate.bat
    echo    Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
    echo    Checking dependencies...
    pip install -q -r requirements.txt
)

echo    Starting backend server...
start "Backend API" cmd /k "call venv\Scripts\activate.bat && python -m uvicorn main:app --reload --port 8000"
cd ..

echo.
echo 2️⃣ Setup & Start Frontend...
cd frontend
if not exist node_modules (
    echo    Installing dependencies...
    call npm install
)

echo    Starting frontend server...
start "Frontend UI" cmd /k "npm run dev"
cd ..

echo.
echo ========================================
echo ✅ System is running!
echo    Frontend: http://localhost:3000
echo    Backend:  http://localhost:8000
echo ========================================
pause
