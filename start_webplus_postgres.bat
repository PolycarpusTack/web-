@echo off
echo Starting Web+ with PostgreSQL (port 5433)
echo.

REM Check if PostgreSQL is accessible
echo Checking PostgreSQL connection...
powershell -Command "Test-NetConnection -ComputerName localhost -Port 5433" >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Cannot connect to PostgreSQL on port 5433
    echo Please ensure PostgreSQL is running
    pause
)

REM Install Python dependencies if needed
echo Checking Python dependencies...
cd apps\backend
pip show asyncpg >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PostgreSQL Python driver...
    pip install asyncpg psycopg2-binary
)

REM Initialize database if needed
cd ..\..
echo Initializing database...
python init_postgres.py
if %errorlevel% neq 0 (
    echo Database initialization failed!
    pause
    exit /b 1
)

REM Start backend
echo.
echo Starting backend server on port 8002...
start cmd /k "cd apps\backend && echo Backend starting... && python -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload"

REM Wait for backend to start
timeout /t 5 /nobreak > nul

REM Start frontend
echo.
echo Starting frontend on port 5173...
cd apps\frontend
call npm install
call npm run dev
