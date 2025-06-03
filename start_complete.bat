@echo off
echo ======================================================
echo        Complete Web+ Launch Solution
echo ======================================================
echo.

REM Set path variables
set PROJECT_DIR=%~dp0
set BACKEND_DIR=%PROJECT_DIR%apps\backend
set FRONTEND_DIR=%PROJECT_DIR%apps\frontend

echo Setting up the environment...
echo.

REM Check Python version
python --version
if %ERRORLEVEL% NEQ 0 (
    echo Python not found! Please install Python 3.9 or higher.
    goto :error
)

REM Check if virtual environment exists, create if not
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
call .venv\Scripts\activate

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install specific versions of problematic packages first
echo Installing specific versions of key packages...
pip install sqlalchemy==1.4.46 aiosqlite==0.18.0 databases[sqlite]==0.7.0 

REM Install all requirements
echo Installing all requirements...
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    pip install fastapi uvicorn alembic pydantic-settings httpx cachetools prometheus-fastapi-instrumentator python-jose python-multipart passlib[bcrypt] pytest pytest-asyncio pytest-cov black isort flake8
)

echo.
echo Installing frontend dependencies...
cd %FRONTEND_DIR%
call npm install
cd %PROJECT_DIR%

REM Create or modify the database.py file with proper SQLite settings
echo Ensuring correct database configuration...
>"%BACKEND_DIR%\db\database_fixed.py" (
    echo from sqlalchemy import create_engine
    echo from sqlalchemy.ext.declarative import declarative_base
    echo from sqlalchemy.orm import sessionmaker
    echo from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    echo import os
    echo from dotenv import load_dotenv
    echo.
    echo # Load environment variables
    echo load_dotenv^(^)
    echo.
    echo # Get database URL from environment or use default SQLite database
    echo db_file = os.path.join^(os.path.dirname^(os.path.dirname^(os.path.abspath^(__file__^)^)^), "web_plus.db"^)
    echo DATABASE_URL = os.getenv^("DATABASE_URL", f"sqlite+aiosqlite:///{db_file}"^)
    echo.
    echo # Create async engine for modern SQLAlchemy style
    echo engine = create_async_engine^(
    echo     DATABASE_URL, 
    echo     echo=False,
    echo     future=True
    echo ^)
    echo.
    echo # Create sessionmaker for creating database sessions
    echo async_session_maker = sessionmaker^(
    echo     engine, 
    echo     class_=AsyncSession, 
    echo     expire_on_commit=False,
    echo     autoflush=False
    echo ^)
    echo.
    echo # Create base class for declarative models
    echo Base = declarative_base^(^)
    echo.
    echo # Dependency for getting the database session
    echo async def get_db^(^):
    echo     """
    echo     Dependency function that yields db sessions
    echo     """
    echo     async with async_session_maker^(^) as session:
    echo         try:
    echo             yield session
    echo             await session.commit^(^)
    echo         except Exception:
    echo             await session.rollback^(^)
    echo             raise
    echo         finally:
    echo             await session.close^(^)
    echo.
    echo # For synchronous use (e.g., in migrations)
    echo SYNC_DATABASE_URL = DATABASE_URL.replace^("aiosqlite", "sqlite"^)
    echo sync_engine = create_engine^(SYNC_DATABASE_URL, echo=False^)
    echo SessionLocal = sessionmaker^(autocommit=False, autoflush=False, bind=sync_engine^)
)

REM Backup the original database.py just in case
if exist "%BACKEND_DIR%\db\database.py" (
    if not exist "%BACKEND_DIR%\db\database.py.bak" (
        copy "%BACKEND_DIR%\db\database.py" "%BACKEND_DIR%\db\database.py.bak"
    )
    copy "%BACKEND_DIR%\db\database_fixed.py" "%BACKEND_DIR%\db\database.py"
)

echo.
echo Starting backend and frontend...
echo.

REM First try to start the backend using Python script
start cmd /k "cd /d %BACKEND_DIR% && call %PROJECT_DIR%.venv\Scripts\activate && echo Starting backend server... && python main.py"

REM Wait for backend to start
echo Waiting for backend to initialize (5 seconds)...
timeout /t 5 /nobreak >nul

REM Start frontend
echo Starting frontend...
start cmd /k "cd /d %FRONTEND_DIR% && echo Starting frontend... && npm run dev"

echo.
echo Web+ is now running:
echo - Backend API: http://localhost:8000
echo - API Documentation: http://localhost:8000/docs
echo - Frontend UI: http://localhost:5173
echo.
echo Press any key to terminate all Web+ processes...
pause >nul

echo Shutting down Web+ services...
taskkill /f /im node.exe >nul 2>&1
REM Find and kill any Python processes running main.py
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /v ^| findstr "main.py"') do (
    taskkill /f /pid %%i >nul 2>&1
)
goto :end

:error
echo.
echo Error occurred during startup! Please check the messages above.
echo.
pause

:end
