#!/bin/bash

# IMDAI Start Script for macOS
# This script starts both backend and frontend servers

set -e  # Exit on error

echo "=========================================="
echo "Starting IMDAI - POD Merch Swarm"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "❌ Error: backend/.env file not found!"
    echo "Please run ./install_mac.sh first and configure your OPENAI_API_KEY"
    exit 1
fi

# Check if OPENAI_API_KEY is set
if grep -q "your-api-key-here" backend/.env; then
    echo "⚠️  Warning: OPENAI_API_KEY appears to be unconfigured in backend/.env"
    echo "Please edit backend/.env and add your actual API key"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo "✓ Servers stopped"
    exit 0
}

# Set up trap to catch Ctrl+C and cleanup
trap cleanup INT TERM

# Start Backend
echo "Starting Backend Server..."
cd backend
source venv/bin/activate
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Check if backend is running
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "❌ Backend failed to start. Check backend.log for details."
    exit 1
fi

echo "✓ Backend running on http://127.0.0.1:8000 (PID: $BACKEND_PID)"

# Start Frontend
echo "Starting Frontend Server..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 3

# Check if frontend is running
if ! ps -p $FRONTEND_PID > /dev/null; then
    echo "❌ Frontend failed to start. Check frontend.log for details."
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo "✓ Frontend running on http://localhost:5173 (PID: $FRONTEND_PID)"
echo ""
echo "=========================================="
echo "IMDAI is now running! ✨"
echo "=========================================="
echo ""
echo "Frontend: http://localhost:5173"
echo "Backend:  http://127.0.0.1:8000"
echo "API Docs: http://127.0.0.1:8000/docs"
echo ""
echo "Logs are being written to:"
echo "  - backend.log"
echo "  - frontend.log"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for user to press Ctrl+C
wait
