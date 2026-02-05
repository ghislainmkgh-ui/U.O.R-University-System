@echo off
REM Setup Script for Access Management Features
REM Run this after SQL migration

echo ================================================
echo Access Management Setup - U.O.R System
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python first.
    pause
    exit /b 1
)

echo [1/5] Checking Python installation...
python --version
echo.

echo [2/5] Installing required packages...
pip install twilio face-recognition
if errorlevel 1 (
    echo [WARNING] Some packages failed to install. Check errors above.
)
echo.

echo [3/5] Verifying MySQL connection...
python -c "from core.database.connection import DatabaseConnection; db = DatabaseConnection(); print('MySQL connection: OK')" 2>nul
if errorlevel 1 (
    echo [WARNING] MySQL connection failed. Check config/settings.py
) else (
    echo MySQL connection: OK
)
echo.

echo [4/5] Checking migration status...
python database/migrations/migration_helper.py --check 2>nul
if errorlevel 1 (
    echo [INFO] Run migration_helper.py manually for detailed status
)
echo.

echo [5/5] Setup Summary
echo ================================================
echo REQUIRED ACTIONS:
echo.
echo 1. Run SQL Migration:
echo    mysql -u [user] -p [database] ^< database/migrations/add_access_management_features.sql
echo.
echo 2. Run Python Helper:
echo    cd database/migrations
echo    python migration_helper.py
echo.
echo 3. Configure WhatsApp in config/settings.py:
echo    - WHATSAPP_ACCOUNT_SID
echo    - WHATSAPP_AUTH_TOKEN
echo    - WHATSAPP_FROM
echo.
echo 4. Update student phone numbers in database
echo.
echo 5. Test notifications with test scripts
echo.
echo ================================================
echo For detailed instructions, see:
echo - database/migrations/README.md
echo - IMPLEMENTATION_SUMMARY.md
echo ================================================
echo.

pause
