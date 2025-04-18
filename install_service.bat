@echo off
echo ===================================================
echo  Installing Distributor Tracker as Windows Service
echo ===================================================
echo.

REM Get the current directory path
set "SCRIPT_DIR=%~dp0"
set "SERVICE_NAME=DistributorTracker"

REM Check if admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script requires administrator privileges.
    echo Please right-click and select "Run as administrator".
    pause
    exit /b 1
)

REM Check if Python is installed globally
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python and ensure it's added to your PATH.
    pause
    exit /b 1
)

REM Install required Python packages
echo Installing required dependencies...
pip install -r local_requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Some dependencies might not have installed correctly.
    pause
)

REM Download NSSM if not already present
if not exist "%SCRIPT_DIR%nssm.exe" (
    echo Downloading NSSM (Non-Sucking Service Manager)...
    powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile '%SCRIPT_DIR%nssm.zip'"
    powershell -Command "Expand-Archive -Path '%SCRIPT_DIR%nssm.zip' -DestinationPath '%SCRIPT_DIR%nssm-temp' -Force"
    powershell -Command "Copy-Item '%SCRIPT_DIR%nssm-temp\nssm-2.24\win64\nssm.exe' '%SCRIPT_DIR%'"
    powershell -Command "Remove-Item '%SCRIPT_DIR%nssm-temp' -Recurse -Force"
    powershell -Command "Remove-Item '%SCRIPT_DIR%nssm.zip' -Force"
)

REM Check if service exists and remove it
"%SCRIPT_DIR%nssm.exe" status "%SERVICE_NAME%" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Service already exists. Removing...
    "%SCRIPT_DIR%nssm.exe" stop "%SERVICE_NAME%"
    "%SCRIPT_DIR%nssm.exe" remove "%SERVICE_NAME%" confirm
)

REM Create the wrapper script
echo @echo off > "%SCRIPT_DIR%service_wrapper.bat"
echo cd /d "%SCRIPT_DIR%" >> "%SCRIPT_DIR%service_wrapper.bat"
echo set DATABASE_PATH=%SCRIPT_DIR%instance\distributor_tracker.db >> "%SCRIPT_DIR%service_wrapper.bat"
echo python main.py >> "%SCRIPT_DIR%service_wrapper.bat"

REM Create service using NSSM
echo Installing service...
"%SCRIPT_DIR%nssm.exe" install "%SERVICE_NAME%" "%SCRIPT_DIR%service_wrapper.bat"
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" DisplayName "Distributor Tracker Service"
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" Description "Enterprise Distributor Tracking and Sales Management Application"
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" Start SERVICE_AUTO_START
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" AppStdout "%SCRIPT_DIR%logs\service.log"
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" AppStderr "%SCRIPT_DIR%logs\service_error.log"
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" AppRotateFiles 1
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" AppRotateSeconds 86400
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" AppRotateBytes 1048576

REM Create logs directory
if not exist "%SCRIPT_DIR%logs" mkdir "%SCRIPT_DIR%logs"

REM Start the service
echo Starting service...
"%SCRIPT_DIR%nssm.exe" start "%SERVICE_NAME%"

REM Create desktop shortcut to access the web app
echo Creating desktop shortcut to access the application...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Distributor Tracker.lnk'); $Shortcut.TargetPath = 'http://localhost:8080'; $Shortcut.IconLocation = '%SCRIPT_DIR%generated-icon.png,0'; $Shortcut.Description = 'Open Distributor Tracker Application'; $Shortcut.Save()"

echo.
echo ===================================================
echo  Installation Complete!
echo ===================================================
echo.
echo The Distributor Tracker service has been installed and started!
echo.
echo - Service Name: %SERVICE_NAME%
echo - Service Status: Running
echo - Access URL: http://localhost:8080
echo - Log Files: %SCRIPT_DIR%logs\
echo.
echo A desktop shortcut has been created to access the application.
echo.
echo The service will automatically start when Windows boots.
echo To manage the service, use Windows Services Manager or these commands:
echo.
echo   - Stop service:    sc stop %SERVICE_NAME%
echo   - Start service:   sc start %SERVICE_NAME%
echo   - Check status:    sc query %SERVICE_NAME%
echo.
pause 