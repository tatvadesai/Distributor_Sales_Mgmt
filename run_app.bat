@echo off
echo Starting Sales Dashboard Application...

:: Change to the directory where the script is located
cd /d "%~dp0"

:: Run the Flask application
echo Starting Flask server...
start /B python app_launcher.py

:: Wait for the server to start
timeout /t 5

:: Open the default browser to the application URL
start http://localhost:5001

echo Application is running! You can access it at http://localhost:5001
echo Press Ctrl+C in this window to stop the application.
echo.
echo Note: To backup data, use the backup functionality within the application.
echo.
pause 