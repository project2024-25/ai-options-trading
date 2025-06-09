@echo off
REM Quick Kite Token Refresh Script
REM Location: D:\Omkar\Algo trading bot\ai-options-trading\quick_kite_refresh.bat

title Kite API Token Refresh

echo.
echo ========================================
echo 🔑 KITE API TOKEN REFRESH
echo ========================================
echo.
echo This script helps you quickly refresh your Kite access token
echo (Access tokens expire daily and need to be regenerated)
echo.

cd /d "D:\Omkar\Algo trading bot\ai-options-trading"
call Scripts\activate

echo Starting Zerodha setup tool...
echo.
echo ⚠️  IMPORTANT: Select option 5 (Regenerate access token)
echo.

python setup_zerodha.py

echo.
echo ========================================
echo 🎯 TOKEN REFRESH COMPLETE
echo ========================================
echo.
echo Next steps:
echo 1. Restart your trading services: restart_services.bat
echo 2. Verify connection: python monitor_system.py
echo 3. Start daily trading: start_trading_system.bat
echo.
pause