@echo off
echo ========================================
echo    XORANYX Bot Starter
echo ========================================
echo.

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing requirements...
pip install -r requirements.txt

echo Starting XORANYX Bot...
python bot.py

pause