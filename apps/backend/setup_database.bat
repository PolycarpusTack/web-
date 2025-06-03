@echo off
REM Web+ Database Setup Script for Windows

echo ================================
echo Web+ Database Setup
echo ================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Please run install_windows.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if database module can be imported
python -c "import db.database" >nul 2>&1
if errorlevel 1 (
    echo Database module not available. Please check your installation.
    pause
    exit /b 1
)

echo.
echo Choose setup option:
echo 1. Quick setup (recommended for first time)
echo 2. Check database status only
echo 3. Reset database (WARNING: deletes all data)
echo 4. Add seed data only
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Running quick database setup...
    python setup_database.py
) else if "%choice%"=="2" (
    echo.
    echo Checking database status...
    python -m db.init_database --check
) else if "%choice%"=="3" (
    echo.
    echo WARNING: This will delete ALL database data!
    set /p confirm="Are you sure? Type 'yes' to confirm: "
    if "%confirm%"=="yes" (
        python -m db.init_database --reset --confirm
    ) else (
        echo Reset cancelled.
    )
) else if "%choice%"=="4" (
    echo.
    echo Adding seed data...
    python -m db.init_database --seed
) else (
    echo Invalid choice. Please run the script again.
    pause
    exit /b 1
)

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Start the backend server: python main.py
echo 2. Open http://localhost:8000/docs to see the API documentation
echo.
pause