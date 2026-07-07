#!/bin/bash
echo "Starting Parkinson's Tremor Screening Application..."

# Check for node_modules in Frontend
if [ ! -d "Frontend/node_modules" ]; then
    echo "node_modules not found in Frontend. Installing dependencies..."
    cd Frontend && npm install && cd ..
fi

# Start Backend in the background
echo "Starting FastAPI Backend..."
cd Backend && python run.py &
BACKEND_PID=$!
cd ..

# Start Frontend in the background
echo "Starting Vite Frontend..."
cd Frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo "Application started!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Press Ctrl+C to stop both processes."

# Function to stop background processes on exit
cleanup() {
    echo "Stopping Backend ($BACKEND_PID) and Frontend ($FRONTEND_PID)..."
    kill $BACKEND_PID $FRONTEND_PID
    exit
}

trap cleanup INT TERM

# Keep the script running to monitor
wait
