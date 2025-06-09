@echo off
REM AI Options Trading System - Daily Startup Script (Fixed)
REM Location: D:\Omkar\Algo trading bot\ai-options-trading\start_trading_system.bat

title AI Options Trading System - Daily Startup

echo.
echo =========================================================
echo AI OPTIONS TRADING SYSTEM - DAILY STARTUP
echo %DATE% %TIME%
echo =========================================================
echo.

REM Change to project directory
cd /d "D:\Omkar\Algo trading bot\ai-options-trading"

REM Try different virtual environment activation paths
echo Preparing system...
if exist "Scripts\activate.bat" (
    echo Found virtual environment: Scripts\activate.bat
    call Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo Found virtual environment: venv\Scripts\activate.bat
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo Found virtual environment: .venv\Scripts\activate.bat
    call .venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found - trying without activation
    echo Available directories:
    dir /b | findstr /i script
    dir /b | findstr /i venv
)

echo.
echo Pre-startup Health Check...
echo =========================================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found in PATH
    echo Please activate your virtual environment manually
    pause
    exit /b 1
) else (
    echo Python available
)

REM Check Kite API credentials using a temporary Python file
echo Checking Kite API credentials...
echo import os > temp_check_kite.py
echo from dotenv import load_dotenv >> temp_check_kite.py
echo load_dotenv() >> temp_check_kite.py
echo api_key = os.getenv('KITE_API_KEY') >> temp_check_kite.py
echo access_token = os.getenv('KITE_ACCESS_TOKEN') >> temp_check_kite.py
echo. >> temp_check_kite.py
echo if not api_key or not access_token: >> temp_check_kite.py
echo     print('WARNING: Kite API not configured - will use fallback data') >> temp_check_kite.py
echo     print('   Run: python setup_zerodha.py to configure') >> temp_check_kite.py
echo else: >> temp_check_kite.py
echo     print('SUCCESS: Kite API credentials found') >> temp_check_kite.py
echo     print(f'   API Key: {api_key[:8]}...') >> temp_check_kite.py
echo     print(f'   Token: {access_token[:10]}...') >> temp_check_kite.py

python temp_check_kite.py
del temp_check_kite.py

echo.
REM Quick check for running services
echo Checking for running services...
echo import requests > temp_check_services.py
echo services = [8001, 8002, 8003, 8004, 8005, 8006, 8007] >> temp_check_services.py
echo running = [] >> temp_check_services.py
echo for port in services: >> temp_check_services.py
echo     try: >> temp_check_services.py
echo         response = requests.get(f'http://localhost:{port}/health', timeout=2) >> temp_check_services.py
echo         if response.status_code == 200: >> temp_check_services.py
echo             running.append(port) >> temp_check_services.py
echo     except: >> temp_check_services.py
echo         pass >> temp_check_services.py
echo. >> temp_check_services.py
echo if running: >> temp_check_services.py
echo     print(f'WARNING: Found {len(running)} services already running on ports: {running}') >> temp_check_services.py
echo     print('   These will be restarted...') >> temp_check_services.py
echo else: >> temp_check_services.py
echo     print('SUCCESS: No services currently running - clean startup') >> temp_check_services.py

python temp_check_services.py
del temp_check_services.py

echo.
echo Starting all services...
call restart_services.bat

echo.
echo Checking N8N status...
curl -s http://localhost:5678 >nul 2>&1
if errorlevel 1 (
    echo WARNING: N8N not detected - please start manually if needed
    echo    Docker command: docker run -d --name n8n-trading-live -p 5678:5678 -v n8n_data:/home/node/.n8n --add-host=host.docker.internal:host-gateway n8nio/n8n:latest
) else (
    echo SUCCESS: N8N is running on http://localhost:5678
)

echo.
echo Testing Kite API Connection...
echo =========================================================
echo try: > temp_test_kite.py
echo     from dotenv import load_dotenv >> temp_test_kite.py
echo     from kiteconnect import KiteConnect >> temp_test_kite.py
echo     import os >> temp_test_kite.py
echo     load_dotenv() >> temp_test_kite.py
echo     api_key = os.getenv('KITE_API_KEY') >> temp_test_kite.py
echo     access_token = os.getenv('KITE_ACCESS_TOKEN') >> temp_test_kite.py
echo     if api_key and access_token: >> temp_test_kite.py
echo         kite = KiteConnect(api_key=api_key) >> temp_test_kite.py
echo         kite.set_access_token(access_token) >> temp_test_kite.py
echo         profile = kite.profile() >> temp_test_kite.py
echo         print(f'SUCCESS: Kite API connected: {profile["user_name"]} ({profile["user_id"]})') >> temp_test_kite.py
echo         try: >> temp_test_kite.py
echo             quote = kite.quote(['NSE:NIFTY 50']) >> temp_test_kite.py
echo             nifty_price = quote['NSE:NIFTY 50']['last_price'] >> temp_test_kite.py
echo             print(f'SUCCESS: Live market data: NIFTY at Rs.{nifty_price}') >> temp_test_kite.py
echo         except Exception as e: >> temp_test_kite.py
echo             print(f'WARNING: Market data: {e} (may be outside market hours)') >> temp_test_kite.py
echo     else: >> temp_test_kite.py
echo         print('WARNING: Kite API not configured - using fallback data') >> temp_test_kite.py
echo         print('   Run: python setup_zerodha.py to configure') >> temp_test_kite.py
echo except Exception as e: >> temp_test_kite.py
echo     print(f'ERROR: Kite API error: {e}') >> temp_test_kite.py
echo     print('   Your access token may have expired (they expire daily)') >> temp_test_kite.py
echo     print('   Run: python setup_zerodha.py to regenerate') >> temp_test_kite.py

python temp_test_kite.py
del temp_test_kite.py

echo.
echo Final System Health Check...
echo =========================================================
if exist simple_monitor.py (
    echo Running simplified health check...
    python simple_monitor.py
) else if exist monitor_system.py (
    echo Running basic health check...
    python -c "
import requests
services = [8001, 8002, 8003, 8004, 8005, 8006, 8007]
healthy = 0
total = len(services)
print('Service Status Check:')
for port in services:
    try:
        response = requests.get(f'http://localhost:{port}/health', timeout=8)
        if response.status_code == 200:
            print(f'  [OK] Service on port {port}')
            healthy += 1
        else:
            print(f'  [ERROR] Service on port {port} - HTTP {response.status_code}')
    except requests.exceptions.Timeout:
        print(f'  [WARN] Service on port {port} - STARTING (timeout)')
    except:
        print(f'  [ERROR] Service on port {port} - NOT RUNNING')

print(f'System Health: {healthy}/{total} services running ({healthy/total*100:.1f}%)')
"
) else (
    echo Basic service check:
    curl -s http://localhost:8001/health 2>nul | findstr status
    curl -s http://localhost:8007/health 2>nul | findstr status
)

echo.
echo =========================================================
echo DAILY STARTUP COMPLETE
echo =========================================================
echo.
echo Daily Trading Checklist:
echo   [ ] All services running
echo   [ ] N8N workflows active
echo   [ ] Kite API connected
echo   [ ] Google Sheets accessible
echo   [ ] Slack notifications working
echo.
echo Quick Links:
echo   * N8N Dashboard: http://localhost:5678
echo   * System Health: python monitor_system.py
echo   * Kite Setup: python setup_zerodha.py
echo   * Google Sheets: https://docs.google.com/spreadsheets/d/1WM6NrthrfDDFD8HWEdh1cTcsrAH-DK31hekKY6GPMMo
echo.
echo Happy Trading! Your AI system is ready.
echo.
echo Tips:
echo   * If Kite API shows errors, run: python setup_zerodha.py
echo   * Access tokens expire daily and need regeneration
echo   * Monitor system health with: python monitor_system.py
echo.
pause