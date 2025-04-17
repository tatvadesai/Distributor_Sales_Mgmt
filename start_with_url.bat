@echo off
ECHO Distributor Performance Tracker with Public URL

REM Check if ngrok is installed
ngrok --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO ngrok is not installed or not in PATH. 
    ECHO Please download it from https://ngrok.com/download and follow the setup instructions.
    ECHO Then run this script again.
    PAUSE
    EXIT /B
)

REM Start the Flask app in the background
START run.bat

ECHO.
ECHO Starting ngrok tunnel...
ECHO When ngrok starts, look for "Forwarding" URL - this is what you'll share with users.
ECHO.
ECHO For example: https://abc123.ngrok.io
ECHO.
ECHO Press Ctrl+C in the ngrok window when you want to stop the public URL.
ECHO But keep the application window running if you want local access to continue.
ECHO.
PAUSE
START ngrok http 8080 