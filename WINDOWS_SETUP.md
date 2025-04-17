# Windows Setup Guide for Distributor Tracker

This guide will help you set up the Distributor Tracker application on a Windows system.

## Prerequisites

1. **Install Python 3.8 or newer**:
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
   - Verify installation by opening Command Prompt and typing `python --version`

2. **Install Git (Optional but recommended)**:
   - Download from [git-scm.com](https://git-scm.com/download/win)
   - This allows you to easily update the application in the future

## Installation

1. **Download the Application**:
   - Download and extract the ZIP file to a location of your choice
   - Or use Git: `git clone [repository-url]`

2. **Run the Setup**:
   - Double-click `run.bat` in the application folder
   - The script will automatically install required dependencies
   - If prompted, select option 1 to run on the default port (8080)

3. **Access the Application**:
   - Open your browser and go to: `http://localhost:8080`
   - Login with default credentials (if first time):
     - Username: `admin`
     - Password: `admin123`
   - **Important**: Change the default password immediately after first login

## Sharing the Application on Your Network

See the `URL_SETUP_GUIDE.md` file for detailed instructions on:
- Sharing the application on your local network
- Setting up a permanent domain name
- Creating an easy-to-remember URL

## Troubleshooting

### Port Already in Use

If you see an error about port 8080 being in use:
1. Run `run.bat` again
2. Select option 2 (Run with custom port)
3. Enter a different port (e.g., 8081, 5000, etc.)
4. Access the application at `http://localhost:[your-chosen-port]`

### Package Installation Errors

If you encounter errors during package installation:
1. Open Command Prompt as Administrator
2. Navigate to the application folder
3. Run: `pip install -r local_requirements.txt`
4. Try running `run.bat` again

## Maintenance and Backup

- The application stores data in an SQLite database in the `instance` folder
- To back up your data, copy this file to a safe location regularly
- For more advanced backup options, see the backup instructions in the application UI

## Removing Unnecessary Files

If you want to clean up the project, you can safely remove these Linux-specific files:
- `distributor-tracker.service` (Linux service configuration)
- `run.sh` (Linux bash script)
- `.replit` and `replit.nix` (Replit platform files)

These files are not needed for Windows operation. 