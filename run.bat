@echo off
ECHO Distributor Performance Tracker Startup Script

REM Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO Python is not installed or not in PATH. Please install Python 3.8+ and try again.
    PAUSE
    EXIT /B
)

REM Check if required packages are installed
pip show flask >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO Flask is not installed. Installing required packages...
    pip install -r local_requirements.txt
    IF %ERRORLEVEL% NEQ 0 (
        ECHO Failed to install required packages. Please check your internet connection.
        PAUSE
        EXIT /B
    )
)

REM Ensure database directory exists
IF NOT EXIST instance mkdir instance

ECHO Select an option:
ECHO 1. Run with default port (8080)
ECHO 2. Run with custom port
ECHO 3. Exit

SET /P option=Enter option (1-3): 

IF "%option%"=="1" (
    ECHO Starting server on port 8080...
    SET FLASK_APP=app.py
    SET FLASK_DEBUG=True
    python -m flask run --host=0.0.0.0 --port=8080
) ELSE IF "%option%"=="2" (
    SET /P custom_port=Enter custom port: 
    ECHO Starting server on port %custom_port%...
    SET FLASK_APP=app.py
    SET FLASK_DEBUG=True
    python -m flask run --host=0.0.0.0 --port=%custom_port%
) ELSE IF "%option%"=="3" (
    ECHO Exiting...
    EXIT /B
) ELSE (
    ECHO Invalid option. Please choose 1, 2, or 3.
    PAUSE
)

PAUSE 