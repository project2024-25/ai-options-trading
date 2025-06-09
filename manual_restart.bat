@echo off
echo ========================================================
echo Manual Data Acquisition Service Restart
echo ========================================================
echo.

REM Navigate to project directory
cd /d "D:\Omkar\Algo trading bot\ai-options-trading"

echo Stopping any existing Data Acquisition processes...
taskkill /f /fi "WINDOWTITLE eq Data Acquisition*" >nul 2>&1
timeout /t 3

echo Starting Data Acquisition service with fresh credentials...
start "Data Acquisition - LIVE" cmd /k "cd services\data-acquisition\app && python main.py"

echo Waiting for service to start...
timeout /t 10

echo Testing live data connection...
curl -s http://localhost:8001/api/data/nifty-snapshot

echo.
echo Service restarted with fresh Kite API credentials!
echo Check the new window for any startup messages.
pause