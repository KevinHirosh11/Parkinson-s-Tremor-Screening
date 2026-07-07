@echo off
echo Starting Parkinson's Tremor Screening Application...

:: Check for node_modules in Frontend
if not exist "Frontend\node_modules\" (
    echo node_modules not found in Frontend. Installing dependencies...
    cd Frontend
    call npm install
    cd ..
)

:: Start Backend in a new window/process
echo Starting FastAPI Backend...
start "Backend - FastAPI" cmd /k "cd Backend && python run.py"

:: Start Frontend in a new window/process
echo Starting Vite Frontend...
start "Frontend - Vite" cmd /k "cd Frontend && npm run dev"

echo Application started!
echo Backend is starting up. Check the opened terminal windows for logs.
pause
