@echo off
REM AI Options Trading Agent - Windows Directory Setup Script
REM Run this script from: D:\Omkar\Algo trading bot\ai-options-trading

echo Creating AI Options Trading Agent directory structure...

REM Create main service directories and subdirectories
mkdir services\data-acquisition\app\models
mkdir services\data-acquisition\app\api
mkdir services\data-acquisition\app\core
mkdir services\data-acquisition\app\services

mkdir services\technical-analysis\app\models
mkdir services\technical-analysis\app\api
mkdir services\technical-analysis\app\core
mkdir services\technical-analysis\app\services

mkdir services\ml-service\app\models
mkdir services\ml-service\app\api
mkdir services\ml-service\app\core
mkdir services\ml-service\app\services

mkdir services\strategy-engine\app\models
mkdir services\strategy-engine\app\api
mkdir services\strategy-engine\app\core
mkdir services\strategy-engine\app\services

mkdir services\risk-management\app\models
mkdir services\risk-management\app\api
mkdir services\risk-management\app\core
mkdir services\risk-management\app\services

mkdir services\options-analytics\app\models
mkdir services\options-analytics\app\api
mkdir services\options-analytics\app\core
mkdir services\options-analytics\app\services

REM Create N8N workflow directories
mkdir n8n-workflows\data-collection
mkdir n8n-workflows\signal-generation
mkdir n8n-workflows\trade-execution
mkdir n8n-workflows\monitoring
mkdir n8n-workflows\templates

REM Create React dashboard directories
mkdir react-dashboard\src\components
mkdir react-dashboard\src\pages
mkdir react-dashboard\src\hooks
mkdir react-dashboard\src\utils
mkdir react-dashboard\src\services
mkdir react-dashboard\public

REM Create Google Sheets directories
mkdir google-sheets\templates
mkdir google-sheets\scripts
mkdir google-sheets\credentials

REM Create Slack bot directories
mkdir slack-bot\app\handlers
mkdir slack-bot\app\commands
mkdir slack-bot\app\utils

REM Create Docker directories
mkdir docker\nginx

REM Create documentation directories
mkdir docs\api
mkdir docs\architecture
mkdir docs\deployment
mkdir docs\user-guide

REM Create test directories
mkdir tests\unit
mkdir tests\integration
mkdir tests\fixtures

REM Create script directories
mkdir scripts\setup
mkdir scripts\deployment
mkdir scripts\maintenance

REM Create log and data directories
mkdir logs
mkdir data\historical
mkdir data\backtest
mkdir data\live
mkdir cache
mkdir backups
mkdir exports

echo.
echo Directory structure created successfully!
echo.
echo Creating Python __init__.py files...

REM Create __init__.py files for Python packages
echo. > services\data-acquisition\app\__init__.py
echo. > services\data-acquisition\app\models\__init__.py
echo. > services\data-acquisition\app\api\__init__.py
echo. > services\data-acquisition\app\core\__init__.py
echo. > services\data-acquisition\app\services\__init__.py

echo. > services\technical-analysis\app\__init__.py
echo. > services\technical-analysis\app\models\__init__.py
echo. > services\technical-analysis\app\api\__init__.py
echo. > services\technical-analysis\app\core\__init__.py
echo. > services\technical-analysis\app\services\__init__.py

echo. > services\ml-service\app\__init__.py
echo. > services\ml-service\app\models\__init__.py
echo. > services\ml-service\app\api\__init__.py
echo. > services\ml-service\app\core\__init__.py
echo. > services\ml-service\app\services\__init__.py

echo. > services\strategy-engine\app\__init__.py
echo. > services\strategy-engine\app\models\__init__.py
echo. > services\strategy-engine\app\api\__init__.py
echo. > services\strategy-engine\app\core\__init__.py
echo. > services\strategy-engine\app\services\__init__.py

echo. > services\risk-management\app\__init__.py
echo. > services\risk-management\app\models\__init__.py
echo. > services\risk-management\app\api\__init__.py
echo. > services\risk-management\app\core\__init__.py
echo. > services\risk-management\app\services\__init__.py

echo. > services\options-analytics\app\__init__.py
echo. > services\options-analytics\app\models\__init__.py
echo. > services\options-analytics\app\api\__init__.py
echo. > services\options-analytics\app\core\__init__.py
echo. > services\options-analytics\app\services\__init__.py

echo. > slack-bot\app\__init__.py
echo. > slack-bot\app\handlers\__init__.py
echo. > slack-bot\app\commands\__init__.py
echo. > slack-bot\app\utils\__init__.py

echo.
echo Python package files created successfully!
echo.
echo Next steps:
echo 1. Copy .env.template to .env and update with your credentials
echo 2. Initialize git repository: git init
echo 3. Create first commit: git add . && git commit -m "Initial project structure"
echo.
echo Setup complete!