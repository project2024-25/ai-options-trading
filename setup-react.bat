@echo off
echo 📱 Setting up React Dashboard...
echo ===============================

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found. Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo ✅ Node.js found

REM Create React app if it doesn't exist
if not exist "react-dashboard" (
    echo 📦 Creating React application...
    call npx create-react-app react-dashboard --template typescript
    
    if errorlevel 1 (
        echo ❌ Failed to create React app
        pause
        exit /b 1
    )
    
    echo ✅ React app created successfully
) else (
    echo ✅ React dashboard directory already exists
)

cd react-dashboard

REM Install dependencies
echo 📦 Installing React dependencies...
call npm install @reduxjs/toolkit react-redux @tanstack/react-query react-router-dom @mui/material @emotion/react @emotion/styled @mui/x-charts @mui/x-data-grid @mui/icons-material @mui/lab axios socket.io-client recharts lightweight-charts date-fns lodash @types/lodash @types/node @types/react @types/react-dom

if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully

REM Create .env file
echo 🔧 Creating environment configuration...
(
echo REACT_APP_API_BASE_URL_DATA=http://localhost:8001
echo REACT_APP_API_BASE_URL_ANALYSIS=http://localhost:8002
echo REACT_APP_API_BASE_URL_ML=http://localhost:8003
echo REACT_APP_API_BASE_URL_STRATEGY=http://localhost:8004
echo REACT_APP_API_BASE_URL_RISK=http://localhost:8005
echo REACT_APP_API_BASE_URL_OPTIONS=http://localhost:8006
echo REACT_APP_WEBSOCKET_URL=ws://localhost:8001/ws
) > .env

echo ✅ Environment file created

REM Create directory structure
echo 📁 Creating project structure...
mkdir src\components\common 2>nul
mkdir src\components\charts 2>nul
mkdir src\components\layout 2>nul
mkdir src\components\modals 2>nul
mkdir src\pages\MarketOverview\components 2>nul
mkdir src\pages\StrategySignals 2>nul
mkdir src\pages\Portfolio 2>nul
mkdir src\pages\OptionsAnalysis 2>nul
mkdir src\store\slices 2>nul
mkdir src\store\api 2>nul
mkdir src\hooks 2>nul
mkdir src\utils 2>nul
mkdir src\types 2>nul
mkdir src\services 2>nul

echo ✅ Project structure created

cd ..

echo.
echo 🎉 React Dashboard Setup Complete!
echo =================================
echo.
echo Next steps:
echo 1. Copy the provided React code files to their respective locations
echo 2. Run 'startup.bat' to start all services
echo 3. Access dashboard at http://localhost:3000
echo.
echo Files to create:
echo • src\services\api.ts
echo • src\store\index.ts
echo • src\App.tsx
echo • src\components\layout\Layout.tsx
echo • And other component files as provided
echo.
pause