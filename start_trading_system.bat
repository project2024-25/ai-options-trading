@echo off
REM AI Options Trading System - Daily Startup Script
REM Location: D:\Omkar\Algo trading bot\ai-options-trading\start_trading_system.bat

title AI Options Trading System - Daily Startup

echo.
echo =========================================================
echo 🤖 AI OPTIONS TRADING SYSTEM - DAILY STARTUP
echo 📅 %DATE% %TIME%
echo =========================================================
echo.

REM Change to project directory
cd /d "D:\Omkar\Algo trading bot\ai-options-trading"

REM Activate virtual environment
echo 🔧 Preparing system...
call Scripts\activate

echo.
echo 🔍 Pre-startup Health Check...
echo =========================================================

REM Quick check for any running services
echo 📊 Checking for running services...
python -c "
import requests
services = [8001, 8002, 8003, 8004, 8005, 8006, 8007]
running = []
for port in services:
    try:
        response = requests.get(f'http://localhost:{port}/health', timeout=2)
        if response.status_code == 200:
            running.append(port)
    except:
        pass

if running:
    print(f'⚠️  Found {len(running)} services already running on ports: {running}')
    print('   These will be restarted...')
else:
    print('✅ No services currently running - clean startup')
"

echo.
echo 🚀 Starting all services...
call restart_services.bat

echo.
echo 🔄 Checking N8N status...
curl -s http://localhost:5678 >nul 2>&1
if errorlevel 1 (
    echo ⚠️  N8N not detected - please start manually if needed
    echo    Docker command: docker run -d --name n8n-trading-live -p 5678:5678 -v n8n_data:/home/node/.n8n --add-host=host.docker.internal:host-gateway n8nio/n8n:latest
) else (
    echo ✅ N8N is running on http://localhost:5678
)

echo.
echo 📊 Final System Health Check...
echo =========================================================
python monitor_system.py

echo.
echo =========================================================
echo 🎯 DAILY STARTUP COMPLETE
echo =========================================================
echo.
echo 📝 Daily Trading Checklist:
echo   [ ] All services running ✅
echo   [ ] N8N workflows active ✅
echo   [ ] Kite API connected ✅
echo   [ ] Google Sheets accessible ✅
echo   [ ] Slack notifications working ✅
echo.
echo 🔗 Quick Links:
echo   • N8N Dashboard: http://localhost:5678
echo   • System Health: python monitor_system.py
echo   • Google Sheets: https://docs.google.com/spreadsheets/d/1WM6NrthrfDDFD8HWEdh1cTcsrAH-DK31hekKY6GPMMo
echo.
echo 📈 Happy Trading! Your AI system is ready.
echo.
pause