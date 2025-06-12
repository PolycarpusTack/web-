@echo off
cd /d C:\Projects\web-plus\apps\backend
echo Starting Web+ Backend on port 8002...
python -m uvicorn main:app --host 0.0.0.0 --port 8002
pause
