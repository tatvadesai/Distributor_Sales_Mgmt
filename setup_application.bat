@echo off
echo Creating Desktop Shortcut for Distributor Tracker...

REM Get the current directory path
set "SCRIPT_DIR=%~dp0"
set "SHORTCUT_NAME=Distributor Tracker.lnk"

REM Check if Python is installed globally
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python and ensure it's added to your PATH.
    pause
    exit /b 1
)

REM Create desktop shortcut using PowerShell
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\%SHORTCUT_NAME%'); $Shortcut.TargetPath = '%SCRIPT_DIR%run_app.bat'; $Shortcut.IconLocation = '%SCRIPT_DIR%generated-icon.png,0'; $Shortcut.Description = 'Launch Distributor Tracker Application'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.Save()"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create desktop shortcut.
    pause
    exit /b 1
)

echo Desktop Shortcut Created!

REM Install dependencies once during setup
echo Installing required dependencies...
pip install -r local_requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Some dependencies might not have installed correctly.
    echo The application may not work properly.
    pause
)

REM Create the run_app.bat file that will be launched by the shortcut
echo @echo off > "%SCRIPT_DIR%run_app.bat"
echo echo Starting Distributor Tracker... >> "%SCRIPT_DIR%run_app.bat"
echo cd /d "%SCRIPT_DIR%" >> "%SCRIPT_DIR%run_app.bat"
echo. >> "%SCRIPT_DIR%run_app.bat"
echo echo Checking database... >> "%SCRIPT_DIR%run_app.bat"
echo python -c "import os; os.path.exists('instance/distributor_tracker.db') or __import__('init_db').setup_db()" >> "%SCRIPT_DIR%run_app.bat"
echo if %%ERRORLEVEL%% NEQ 0 ( >> "%SCRIPT_DIR%run_app.bat"
echo    echo ERROR: Database initialization failed. >> "%SCRIPT_DIR%run_app.bat"
echo    pause >> "%SCRIPT_DIR%run_app.bat"
echo    exit /b 1 >> "%SCRIPT_DIR%run_app.bat"
echo ) >> "%SCRIPT_DIR%run_app.bat"
echo. >> "%SCRIPT_DIR%run_app.bat"
echo echo Starting application... >> "%SCRIPT_DIR%run_app.bat"
echo python main.py >> "%SCRIPT_DIR%run_app.bat"
echo if %%ERRORLEVEL%% NEQ 0 ( >> "%SCRIPT_DIR%run_app.bat"
echo    echo. >> "%SCRIPT_DIR%run_app.bat"
echo    echo ERROR: The application crashed or failed to start properly. >> "%SCRIPT_DIR%run_app.bat"
echo    echo Please contact IT support for assistance. >> "%SCRIPT_DIR%run_app.bat"
echo ) >> "%SCRIPT_DIR%run_app.bat"
echo pause >> "%SCRIPT_DIR%run_app.bat"

echo Setup Complete!
echo You can now launch the application from the desktop shortcut.

REM Ask if the user wants to start the application now
set /p START_NOW="Do you want to start the application now? (Y/N): "
if /i "%START_NOW%"=="Y" (
    call "%SCRIPT_DIR%run_app.bat"
)

pause 