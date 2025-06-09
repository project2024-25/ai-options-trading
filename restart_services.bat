@echo off
REM AI Options Trading System - Service Restart Script
REM Location: D:\Omkar\Algo trading bot\ai-options-trading\restart_services.bat

echo.
echo =========================================================
echo 🤖 AI OPTIONS TRADING SYSTEM - SERVICE RESTART
echo =========================================================
echo.

REM Change to project directory
cd /d "D:\Omkar\Algo trading bot\ai-options-trading"

REM Check if virtual environment exists
if not exist "Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    echo Please check the project path and virtual environment.
    pause
    exit /b 1
)

echo 📁 Project Directory: %CD%
echo.

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call Scripts\activate
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)
echo ✅ Virtual environment activated
echo.

REM Kill existing Python processes (trading services only)
echo 🛑 Stopping existing services...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| find "python.exe"') do (
    echo   • Stopping Python process...
    taskkill /F /PID %%i >nul 2>&1
)
echo ✅ Existing services stopped
echo.

REM Wait for cleanup
echo ⏱️  Waiting for cleanup...
timeout /t 5 /nobreak >nul
echo.

REM Start services in separate windows
echo 🚀 Starting AI Trading Services...
echo.

echo 📊 Starting Data Acquisition Service (Port 8001)...
start "🔵 Data Acquisition (8001)" cmd /k "title Data Acquisition Service && cd services\data-acquisition\app && echo Starting Data Acquisition Service... && python main.py"
timeout /t 3 /nobreak >nul

echo 📈 Starting Technical Analysis Service (Port 8002)...
start "🟢 Technical Analysis (8002)" cmd /k "title Technical Analysis Service && cd services\technical-analysis\app && echo Starting Technical Analysis Service... && python main.py"
timeout /t 3 /nobreak >nul

echo 🧠 Starting ML Service (Port 8003)...
start "🟡 ML Service (8003)" cmd /k "title ML Service && cd services\ml-service\app && echo Starting ML Service... && python main.py"
timeout /t 3 /nobreak >nul

echo ⚡ Starting Strategy Engine (Port 8004)...
start "🟠 Strategy Engine (8004)" cmd /k "title Strategy Engine && cd services\strategy-engine\app && echo Starting Strategy Engine... && python main.py"
timeout /t 3 /nobreak >nul

echo 🛡️  Starting Risk Management Service (Port 8005)...
start "🔴 Risk Management (8005)" cmd /k "title Risk Management Service && cd services\risk-management\app && echo Starting Risk Management Service... && python main.py"
timeout /t 3 /nobreak >nul

echo 📊 Starting Options Analytics Service (Port 8006)...
start "🟣 Options Analytics (8006)" cmd /k "title Options Analytics Service && cd services\options-analytics\app && echo Starting Options Analytics Service... && python main.py"
timeout /t 3 /nobreak >nul

echo 💼 Starting Order Execution Service (Port 8007)...
start "🔶 Order Execution (8007)" cmd /k "title Order Execution Service && cd services\order-execution\app && echo Starting Order Execution Service... && python main.py"
timeout /t 3 /nobreak >nul

echo.
echo ✅ All services started in separate windows!
echo.

echo 📋 Service Status:
echo   • Data Acquisition    : Port 8001 (Blue window)
echo   • Technical Analysis  : Port 8002 (Green window)  
echo   • ML Service         : Port 8003 (Yellow window)
echo   • Strategy Engine    : Port 8004 (Orange window)
echo   • Risk Management    : Port 8005 (Red window)
echo   • Options Analytics  : Port 8006 (Purple window)
echo   • Order Execution    : Port 8007 (Brown window)
echo.

echo ⏱️  Waiting for services to initialize...
timeout /t 10 /nobreak >nul

echo 🔍 Running health check...
python monitor_system.py
echo.

echo =========================================================
echo 🎯 STARTUP COMPLETE
echo =========================================================
echo.
echo 📝 Next Steps:
echo   1. Check that all service windows are running
echo   2. Verify N8N is running (http://localhost:5678)
echo   3. Test your workflows
echo   4. Monitor system health regularly
echo.
echo Press any key to exit...
pause >nul