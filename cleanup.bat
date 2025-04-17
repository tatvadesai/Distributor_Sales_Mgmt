@echo off
ECHO Cleaning up unnecessary files...

REM Remove Linux-specific files
DEL /Q distributor-tracker.service
DEL /Q run.sh
DEL /Q .replit
DEL /Q replit.nix
DEL /Q uv.lock

REM Remove old documentation
DEL /Q README.md
DEL /Q INSTALL.md
DEL /Q env_setup_instructions.md

REM Remove migration and initialization tools
DEL /Q migrate_target_table.py
DEL /Q init_db.py
DEL /Q main.py

REM Rename and keep only the Windows documentation
ECHO Creating a single README file with essential information...
COPY WINDOWS_SETUP.md README.md

ECHO Done! The following files have been kept:
ECHO - app.py (Main application)
ECHO - routes.py (Application routes)
ECHO - models.py (Database models)
ECHO - utils.py (Utility functions)
ECHO - wsgi.py (WSGI entry point)
ECHO - templates/ (HTML templates)
ECHO - static/ (CSS/JS assets)
ECHO - instance/ (Database directory)
ECHO - backup_utils.py (Backup functionality)
ECHO - run.bat (Windows startup script)
ECHO - start_with_url.bat (Public URL script)
ECHO - URL_SETUP_GUIDE.md (URL configuration guide)
ECHO - README.md (Installation instructions)
ECHO - local_requirements.txt (Dependencies)
ECHO - .env & .env.production (Environment configurations)

PAUSE 