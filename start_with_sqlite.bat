@echo off
echo Initializing Web+ Database and Starting Services
echo.

REM Initialize the database using pure SQLite
echo Initializing database with SQLite...
python init_db_sqlite.py

REM Create separate window for the backend
echo.
echo Starting backend...
start cmd /k "cd /d %~dp0 && echo Starting backend server... && python backend_sync.py"

REM Wait a moment for backend to initialize
echo Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

REM Start frontend in this window
echo.
echo Starting frontend...
cd /d %~dp0\apps\frontend
call npm install
call npm run dev
