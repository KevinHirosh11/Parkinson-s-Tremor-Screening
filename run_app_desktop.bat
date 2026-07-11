@echo off
echo Starting Parkinson's Tremor Screening Application (Desktop Mode)...

if not exist "Frontend\node_modules\" (
    echo node_modules not found in Frontend. Installing dependencies...
    cd Frontend
    call npm install
    cd ..
)

echo Launching the App interface...
cd Frontend
npm run desktop

echo Application closed!
pause
