@echo off
REM Setup script for Distributor Tracker application
REM This script will set up a Python virtual environment and install all required dependencies

echo Setting up Distributor Tracker Application...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in your PATH.
    echo Please install Python 3.8 or higher from https://www.python.org/downloads/
    echo and make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Create a virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM Activate the virtual environment and install dependencies
echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat

REM Upgrade pip to the latest version
echo Upgrading pip to the latest version...
python -m pip install --upgrade pip

REM Install required packages
echo Installing required packages...
pip install -r requirements.txt

REM Install additional packages explicitly in case the requirements.txt doesn't work
echo Installing critical packages explicitly...
pip install flask flask-login SQLAlchemy Flask-SQLAlchemy

REM Initialize the database if it doesn't exist
if not exist "data.db" (
    echo Initializing the database...
    python init_db.py
    if %errorlevel% neq 0 (
        echo Error: Failed to initialize the database.
        pause
        exit /b 1
    )
)

echo.
echo Setup completed successfully!
echo.
echo To run the application:
echo 1. Open a command prompt in this directory
echo 2. Run: venv\Scripts\activate.bat
echo 3. Run: python app.py
echo.
echo The application will be accessible at http://127.0.0.1:5000
echo.

pause 