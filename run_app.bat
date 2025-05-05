@echo off
echo Starting Sales Dashboard Application...

:: Check if another instance is already running
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq Sales Dashboard" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Application is already running!
    echo Please close the existing instance before starting a new one.
    pause
    exit /b 1
)

:: Change to the directory where the script is located
cd /d "%~dp0"

:: Run the Flask application with a specific window title
start "Sales Dashboard" /B python app_launcher.py

:: Wait for the server to start
timeout /t 5

:: Open the default browser to the application URL
start http://localhost:5001

echo Application is running! You can access it at http://localhost:5001
echo.
echo Note: To backup data, use the backup functionality within the application.
echo.
echo Press Ctrl+C in this window to stop the application.
echo Closing this window will stop the server.

:: Wait for user to close the window
pause

:: Clean up - kill the Python process when the window is closed
taskkill /F /FI "WINDOWTITLE eq Sales Dashboard" /T 