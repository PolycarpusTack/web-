@echo off
echo Starting Web+ with PostgreSQL
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

REM Start PostgreSQL
echo Starting PostgreSQL database...
docker-compose -f docker-compose.postgres.yml up -d

REM Wait for PostgreSQL to be ready
echo Waiting for PostgreSQL to be ready...
timeout /t 10 /nobreak > nul

REM Install Python dependencies
echo Installing Python dependencies...
cd apps\backend
pip install asyncpg psycopg2-binary

REM Run migration if needed
echo Checking database...
cd ..\..
python migrate_to_postgres.py

REM Start backend
echo Starting backend server...
start cmd /k "cd apps\backend && python -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload"

REM Wait for backend
timeout /t 5 /nobreak > nul

REM Start frontend
echo Starting frontend...
cd apps\frontend
npm install
npm run dev
