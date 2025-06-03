@echo off
echo Starting Web+ Frontend with Mock API
echo.
echo This will start the UI with a mock API backend that simulates responses.
echo No actual LLM functionality will be available.
echo.
echo Press any key to continue...
pause > nul

python frontend_with_mock_api.py
