@echo off
echo Starting Web+ (Frontend and Backend)
echo.

REM Create separate window for the backend
start cmd /k "cd /d %~dp0 && echo Starting backend... && python backend_sync.py"

REM Wait a moment for backend to initialize
echo Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

REM Start frontend in this window
echo.
echo Starting frontend...
cd /d %~dp0\apps\frontend
call npm install
call npm run dev
