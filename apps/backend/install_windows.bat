@echo off
REM Windows installation script for Web+ backend
REM This script handles common Windows permission issues

echo ====================================
echo Web+ Backend Installation for Windows
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

echo Python found. Continuing installation...
echo.

REM Upgrade pip first to avoid issues
echo Upgrading pip...
python -m pip install --upgrade pip --user

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip inside virtual environment
python -m pip install --upgrade pip

REM Install requirements one by one to handle permission issues better
echo.
echo Installing dependencies (this may take a few minutes)...
echo.

REM Core dependencies
python -m pip install --no-cache-dir wheel setuptools

REM Install in smaller groups to avoid permission issues
echo Installing FastAPI and core dependencies...
python -m pip install --no-cache-dir fastapi uvicorn httpx python-dotenv pydantic pydantic-settings

echo Installing database dependencies...
python -m pip install --no-cache-dir sqlalchemy alembic aiosqlite asyncpg greenlet

echo Installing authentication dependencies...
python -m pip install --no-cache-dir passlib[bcrypt] python-jose[cryptography] bcrypt email-validator

echo Installing remaining dependencies...
python -m pip install --no-cache-dir -r requirements.txt

REM Create necessary directories
if not exist "uploads" mkdir uploads
if not exist "logs" mkdir logs

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file...
    (
        echo # Web+ Backend Configuration
        echo DATABASE_URL=
        echo SECRET_KEY=your-secret-key-here
        echo ALGORITHM=HS256
        echo ACCESS_TOKEN_EXPIRE_MINUTES=30
        echo ADMIN_EMAIL=admin@example.com
        echo ADMIN_USERNAME=admin
        echo ADMIN_PASSWORD=admin123
    ) > .env
    echo.
    echo IMPORTANT: Please edit the .env file with your configuration
)

echo.
echo ====================================
echo Installation completed!
echo ====================================
echo.
echo Next steps:
echo 1. Edit the .env file with your configuration
echo 2. Run the database test: python test_db_connection.py
echo 3. Initialize the database: python -m db.init_db
echo 4. Start the server: python main.py
echo.
echo If you encounter permission errors, try:
echo - Running Command Prompt as Administrator
echo - Using: python -m pip install --user [package]
echo - Temporarily disabling antivirus software
echo.
pause