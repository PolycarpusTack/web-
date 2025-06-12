@echo off
cd C:\Projects\web-plus\apps\backend

REM Set environment to disable optional features
set WEBPLUS_CACHE_ENABLED=false
set WEBPLUS_JOB_QUEUE_ENABLED=false

echo Starting Web+ Backend with optional features disabled...
python -m uvicorn main:app --host 0.0.0.0 --port 8002 --log-level info
