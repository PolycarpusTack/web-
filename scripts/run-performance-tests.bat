@echo off
setlocal enabledelayedexpansion

echo Running Web+ Performance Tests
echo ================================

:: Check dependencies
echo Checking dependencies...

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Python is not installed
    exit /b 1
)

where node >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Node.js is not installed
    exit /b 1
)

where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: npm is not installed
    exit /b 1
)

echo All dependencies found

:: Backend Performance Tests
echo.
echo Running Backend Performance Tests
echo -----------------------------------

cd apps\backend

:: Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install dependencies
echo Installing backend dependencies...
pip install -r requirements.txt -q

:: Run backend performance tests
echo Running tests...
python -m pytest performance\benchmark.py -v --tb=short

:: Deactivate virtual environment
deactivate

:: Frontend Performance Tests
echo.
echo Running Frontend Performance Tests
echo ------------------------------------

cd ..\frontend

:: Install dependencies
if not exist node_modules (
    echo Installing frontend dependencies...
    npm ci
)

:: Build frontend
echo Building frontend...
npm run build

:: Install Playwright browsers if needed
npx playwright install chromium

:: Start preview server
echo Starting preview server...
start /b npm run preview

:: Wait for server to start
timeout /t 5 /nobreak >nul

:: Run performance tests
echo Running tests...
npx playwright test e2e\performance\performance.spec.ts --reporter=list

:: Kill the preview server
taskkill /f /im node.exe >nul 2>&1

:: Summary
echo.
echo ================================
echo Performance Test Summary
echo ================================
echo.
echo Phase 2 Performance Targets:
echo   - API Response Time: ^< 200ms
echo   - Page Load Time: ^< 3s
echo   - Time to Interactive: ^< 2s
echo   - Bundle Size: ^< 2MB
echo.
echo Performance tests completed!
echo.
echo Tips:
echo   - To enable the performance monitor in the browser, press the 'Show Performance' button
echo   - Check performance_results\ and test-results\ for detailed reports
echo   - Run this script regularly to catch performance regressions early

cd ..\..
endlocal