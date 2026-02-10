#!/bin/bash

echo "🚀 Starting Brain Tumor MRI Analysis System"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

echo ""
echo "1️⃣  Setting up Backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "   Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "   Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "   Installing Python dependencies..."
pip install -q -r requirements.txt

echo "   ✓ Backend setup complete"

# Open new terminal for backend
echo ""
echo "   Starting backend server..."
python main.py &
BACKEND_PID=$!

cd ..

echo ""
echo "2️⃣  Setting up Frontend..."
cd frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "   Installing Node.js dependencies..."
    npm install
fi

echo "   ✓ Frontend setup complete"

# Start frontend
echo ""
echo "   Starting frontend development server..."
npm run dev &
FRONTEND_PID=$!

cd ..

echo ""
echo "=========================================="
echo "✅ System is starting up!"
echo ""
echo "   Backend API:  http://localhost:8000"
echo "   Frontend UI:  http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=========================================="

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
