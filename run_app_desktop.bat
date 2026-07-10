@echo off
echo Starting Parkinson's Tremor Screening Application (Desktop Mode)...

:: Check for node_modules in Frontend
if not exist "Frontend\node_modules\" (
    echo node_modules not found in Frontend. Installing dependencies...
    cd Frontend
    call npm install
    cd ..
)

:: Start the application via Electron (Electron manages the Python backend)
echo Launching the App interface...
cd Frontend
npm run desktop

echo Application closed!
pause
