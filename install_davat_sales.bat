@echo off
REM ============================================================================
REM Davat Beverages Sales Dashboard - Windows Installation Script
REM ============================================================================
setlocal enabledelayedexpansion

echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║                                                                        ║
echo ║                      DAVAT BEVERAGES                                   ║
echo ║                 SALES DASHBOARD INSTALLATION                           ║
echo ║                                                                        ║
echo ╚════════════════════════════════════════════════════════════════════════╝

REM Get the current directory path
set "INSTALL_DIR=%~dp0"
IF %INSTALL_DIR:~-1%==\ SET INSTALL_DIR=%INSTALL_DIR:~0,-1%

set "APP_NAME=Davat Sales Dashboard"
set "SERVICE_NAME=DavatSalesService"
set "LOG_DIR=%INSTALL_DIR%\logs"
set "VENV_DIR=%INSTALL_DIR%\venv"
set "DB_DIR=%INSTALL_DIR%\database"
set "ICON_PATH=%INSTALL_DIR%\generated-icon.png"

REM Check for administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] This script requires administrator privileges.
    echo Please right-click the script and select "Run as administrator".
    echo.
    pause
    exit /b 1
)

REM Create logs directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Start logging
echo Installation started at %date% %time% > "%LOG_DIR%\install_log.txt"

REM Check for Python installation
echo [1/8] Checking for Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo.
    echo Please install Python 3.8 or newer from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    echo After installing Python, run this script again.
    echo [ERROR] Python not found. Installation aborted. >> "%LOG_DIR%\install_log.txt"
    pause
    exit /b 1
)

REM Display Python version
python --version >> "%LOG_DIR%\install_log.txt" 2>&1
echo [SUCCESS] Python is installed.
echo [SUCCESS] Python is installed. >> "%LOG_DIR%\install_log.txt"

REM Create virtual environment
echo [2/8] Setting up Python virtual environment...
if exist "%VENV_DIR%" (
    echo Virtual environment already exists, skipping creation.
) else (
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        echo [ERROR] Failed to create virtual environment. >> "%LOG_DIR%\install_log.txt"
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created.
    echo [SUCCESS] Virtual environment created. >> "%LOG_DIR%\install_log.txt"
)

REM Activate virtual environment
echo [3/8] Activating virtual environment and installing dependencies...
call "%VENV_DIR%\Scripts\activate.bat"

REM Upgrade pip to latest version
python -m pip install --upgrade pip
echo [SUCCESS] Pip upgraded to latest version.
echo [SUCCESS] Pip upgraded to latest version. >> "%LOG_DIR%\install_log.txt"

REM Install the required dependencies
echo [4/8] Installing required packages (this may take a few minutes)...
pip install -r requirements.txt >> "%LOG_DIR%\install_log.txt" 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Some packages may not have installed correctly.
    echo [WARNING] Some packages may not have installed correctly. >> "%LOG_DIR%\install_log.txt"
    
    REM Install critical packages explicitly
    echo Installing critical packages individually...
    echo Installing critical packages individually... >> "%LOG_DIR%\install_log.txt"
    pip install Flask==2.3.3 Flask-Login==0.6.2 SQLAlchemy==2.0.23 Flask-SQLAlchemy==3.1.0 >> "%LOG_DIR%\install_log.txt" 2>&1
    pip install Werkzeug==2.3.7 Jinja2==3.1.3 python-dotenv==1.0.0 >> "%LOG_DIR%\install_log.txt" 2>&1
    pip install reportlab==4.0.8 openpyxl==3.1.2 Flask-WTF==1.2.1 >> "%LOG_DIR%\install_log.txt" 2>&1
    pip install pywin32 >> "%LOG_DIR%\install_log.txt" 2>&1
)

echo [SUCCESS] Dependencies installed.
echo [SUCCESS] Dependencies installed. >> "%LOG_DIR%\install_log.txt"

REM Create database directory if it doesn't exist
echo [5/8] Setting up database...
if not exist "%DB_DIR%" (
    mkdir "%DB_DIR%"
    echo Created database directory.
    echo Created database directory. >> "%LOG_DIR%\install_log.txt"
)

REM Initialize the database if it doesn't exist
if not exist "%DB_DIR%\data.db" (
    echo Initializing the database...
    set "DATABASE_PATH=%DB_DIR%\data.db"
    python init_db.py >> "%LOG_DIR%\install_log.txt" 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to initialize the database.
        echo [ERROR] Failed to initialize the database. >> "%LOG_DIR%\install_log.txt"
        pause
        exit /b 1
    )
    echo [SUCCESS] Database initialized.
    echo [SUCCESS] Database initialized. >> "%LOG_DIR%\install_log.txt"
) else (
    echo [INFO] Database already exists, skipping initialization.
    echo [INFO] Database already exists, skipping initialization. >> "%LOG_DIR%\install_log.txt"
)

REM Create .env file with database configuration
echo Creating .env file with configuration...
echo DATABASE_PATH=%DB_DIR%\data.db > "%INSTALL_DIR%\.env"
echo PORT=5001 >> "%INSTALL_DIR%\.env"
echo FLASK_ENV=production >> "%INSTALL_DIR%\.env"
echo SECRET_KEY=DavatBeveragesSecureKey >> "%INSTALL_DIR%\.env"

REM Create startup script
echo [6/8] Creating application startup script...
echo @echo off > "%INSTALL_DIR%\run_davat_sales.bat"
echo cd /d "%INSTALL_DIR%" >> "%INSTALL_DIR%\run_davat_sales.bat"
echo call "%VENV_DIR%\Scripts\activate.bat" >> "%INSTALL_DIR%\run_davat_sales.bat"
echo set "DATABASE_PATH=%DB_DIR%\data.db" >> "%INSTALL_DIR%\run_davat_sales.bat"
echo python main.py >> "%INSTALL_DIR%\run_davat_sales.bat"
echo pause >> "%INSTALL_DIR%\run_davat_sales.bat"

echo [SUCCESS] Created startup script.
echo [SUCCESS] Created startup script. >> "%LOG_DIR%\install_log.txt"

REM Download NSSM if needed (Non-Sucking Service Manager)
echo [7/8] Setting up Windows service...
if not exist "%INSTALL_DIR%\nssm.exe" (
    echo Downloading NSSM (Non-Sucking Service Manager)...
    powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile '%INSTALL_DIR%\nssm.zip'" >> "%LOG_DIR%\install_log.txt" 2>&1
    powershell -Command "Expand-Archive -Path '%INSTALL_DIR%\nssm.zip' -DestinationPath '%INSTALL_DIR%\nssm-temp' -Force" >> "%LOG_DIR%\install_log.txt" 2>&1
    powershell -Command "Copy-Item '%INSTALL_DIR%\nssm-temp\nssm-2.24\win64\nssm.exe' '%INSTALL_DIR%'" >> "%LOG_DIR%\install_log.txt" 2>&1
    powershell -Command "Remove-Item '%INSTALL_DIR%\nssm-temp' -Recurse -Force" >> "%LOG_DIR%\install_log.txt" 2>&1
    powershell -Command "Remove-Item '%INSTALL_DIR%\nssm.zip' -Force" >> "%LOG_DIR%\install_log.txt" 2>&1
    
    if not exist "%INSTALL_DIR%\nssm.exe" (
        echo [WARNING] Could not download NSSM. Windows service will not be installed.
        echo [WARNING] Could not download NSSM. Windows service will not be installed. >> "%LOG_DIR%\install_log.txt"
    )
)

REM Create service wrapper script
echo @echo off > "%INSTALL_DIR%service_wrapper.bat"
echo cd /d "%INSTALL_DIR%" >> "%INSTALL_DIR%service_wrapper.bat"
echo set "DATABASE_PATH=%DB_DIR%\data.db" >> "%INSTALL_DIR%service_wrapper.bat"
echo call "%VENV_DIR%\Scripts\activate.bat" >> "%INSTALL_DIR%service_wrapper.bat"
echo python main.py >> "%INSTALL_DIR%service_wrapper.bat"

REM Install as Windows service if NSSM is available
if exist "%INSTALL_DIR%\nssm.exe" (
    REM Check if service exists and remove it
    "%INSTALL_DIR%\nssm.exe" status "%SERVICE_NAME%" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo Service already exists. Removing...
        "%INSTALL_DIR%\nssm.exe" stop "%SERVICE_NAME%"
        "%INSTALL_DIR%\nssm.exe" remove "%SERVICE_NAME%" confirm
    )

    REM Install the service
    echo Installing Windows service...
    "%INSTALL_DIR%\nssm.exe" install "%SERVICE_NAME%" "%INSTALL_DIR%\service_wrapper.bat"
    "%INSTALL_DIR%\nssm.exe" set "%SERVICE_NAME%" DisplayName "Davat Beverages Sales Dashboard"
    "%INSTALL_DIR%\nssm.exe" set "%SERVICE_NAME%" Description "Enterprise Sales Management Service for Davat Beverages"
    "%INSTALL_DIR%\nssm.exe" set "%SERVICE_NAME%" Start SERVICE_AUTO_START
    "%INSTALL_DIR%\nssm.exe" set "%SERVICE_NAME%" AppStdout "%LOG_DIR%\service.log"
    "%INSTALL_DIR%\nssm.exe" set "%SERVICE_NAME%" AppStderr "%LOG_DIR%\service_error.log"
    "%INSTALL_DIR%\nssm.exe" set "%SERVICE_NAME%" AppRotateFiles 1
    "%INSTALL_DIR%\nssm.exe" set "%SERVICE_NAME%" AppRotateSeconds 86400
    "%INSTALL_DIR%\nssm.exe" set "%SERVICE_NAME%" AppRotateBytes 1048576

    REM Start the service
    echo Starting Windows service...
    "%INSTALL_DIR%\nssm.exe" start "%SERVICE_NAME%"
    
    if %ERRORLEVEL% EQU 0 (
        echo [SUCCESS] Windows service installed and started.
        echo [SUCCESS] Windows service installed and started. >> "%LOG_DIR%\install_log.txt"
    ) else (
        echo [WARNING] Windows service installation failed.
        echo [WARNING] Windows service installation failed. >> "%LOG_DIR%\install_log.txt"
    )
) else (
    echo [WARNING] NSSM not found, Windows service not installed.
    echo [WARNING] NSSM not found, Windows service not installed. >> "%LOG_DIR%\install_log.txt"
)

REM Create desktop shortcut
echo [8/8] Creating desktop shortcut...
echo Creating desktop shortcut using the Davat Beverages logo...

REM Create a launcher batch file that ensures the service is running
echo @echo off > "%INSTALL_DIR%\open_dashboard.bat"
echo echo Starting Davat Beverages Sales Dashboard... >> "%INSTALL_DIR%\open_dashboard.bat"
echo echo Checking if service is running... >> "%INSTALL_DIR%\open_dashboard.bat"
echo sc query "%SERVICE_NAME%" | findstr RUNNING >nul >> "%INSTALL_DIR%\open_dashboard.bat"
echo if %%ERRORLEVEL%% NEQ 0 ( >> "%INSTALL_DIR%\open_dashboard.bat"
echo   echo Service is not running. Starting service... >> "%INSTALL_DIR%\open_dashboard.bat"
echo   sc start "%SERVICE_NAME%" >nul >> "%INSTALL_DIR%\open_dashboard.bat"
echo   echo Waiting for service to start... >> "%INSTALL_DIR%\open_dashboard.bat"
echo   timeout /t 5 >nul >> "%INSTALL_DIR%\open_dashboard.bat"
echo ) else ( >> "%INSTALL_DIR%\open_dashboard.bat"
echo   echo Service is already running. >> "%INSTALL_DIR%\open_dashboard.bat"
echo ) >> "%INSTALL_DIR%\open_dashboard.bat"
echo echo Opening Davat Beverages Sales Dashboard... >> "%INSTALL_DIR%\open_dashboard.bat"
echo start "" "http://localhost:5001" >> "%INSTALL_DIR%\open_dashboard.bat"
echo exit >> "%INSTALL_DIR%\open_dashboard.bat"

REM Create the desktop shortcut with the Davat Beverages icon
powershell -Command ^
"$WshShell = New-Object -ComObject WScript.Shell; ^
$Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\%APP_NAME%.lnk'); ^
$Shortcut.TargetPath = '%INSTALL_DIR%\open_dashboard.bat'; ^
$Shortcut.IconLocation = '%ICON_PATH%,0'; ^
$Shortcut.WorkingDirectory = '%INSTALL_DIR%'; ^
$Shortcut.Description = 'Open Davat Beverages Sales Dashboard'; ^
$Shortcut.Save()" >> "%LOG_DIR%\install_log.txt" 2>&1

if %errorlevel% neq 0 (
    echo [WARNING] Could not create desktop shortcut.
    echo [WARNING] Could not create desktop shortcut. >> "%LOG_DIR%\install_log.txt"
) else (
    echo [SUCCESS] Desktop shortcut created.
    echo [SUCCESS] Desktop shortcut created. >> "%LOG_DIR%\install_log.txt"
)

REM Installation complete
echo.
echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║                                                                        ║
echo ║               INSTALLATION COMPLETED SUCCESSFULLY!                     ║
echo ║                                                                        ║
echo ╚════════════════════════════════════════════════════════════════════════╝
echo.
echo  Davat Beverages Sales Dashboard has been installed as an enterprise application.
echo.
echo  SERVICE INFORMATION:
echo  - Service Name: %SERVICE_NAME%
echo  - Status: Running as Windows service
echo  - Database Path: %DB_DIR%\data.db
echo  - Log Files: %LOG_DIR%
echo.
echo  ACCESS METHODS:
echo  - Desktop icon: Click the Davat Sales Dashboard icon on your desktop
echo  - Manual URL: http://localhost:5001
echo.
echo  AUTHENTICATION:
echo  - Username: admin
echo  - Password: admin123
echo.
echo  SERVICE MANAGEMENT:
echo  - Start service:   sc start %SERVICE_NAME%
echo  - Stop service:    sc stop %SERVICE_NAME%
echo  - Service status:  sc query %SERVICE_NAME%
echo.
echo Installation completed at %date% %time% >> "%LOG_DIR%\install_log.txt"

pause 