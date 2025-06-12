@echo off
cd C:\Projects\web-plus\apps\backend
echo Starting Web+ Full Backend on port 8003...
python -m uvicorn main:app --host 0.0.0.0 --port 8003 --log-level info
pause
