@echo off
echo Starting Web+ Frontend Only
echo.
echo NOTE: This will only start the UI without the backend functionality.
echo Models, chats and other backend features will not work.
echo.
echo Press any key to continue...
pause > nul

cd apps\frontend
echo.
echo Installing frontend dependencies...
call npm install
echo.
echo Starting frontend...
echo UI will be available at http://localhost:5173
echo.
call npm run dev
